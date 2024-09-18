import logging

from django.core.exceptions import ValidationError
from django.db import models

try:
    from django.db.models.fields.related_descriptors import ForwardManyToOneDescriptor
except ImportError:
    from django.db.models.fields.related import (
        ReverseSingleRelatedObjectDescriptor as ForwardManyToOneDescriptor,
    )

logger = logging.getLogger(__name__)

__all__ = ["Country", "State", "Locality", "Address", "AddressField"]


class InconsistentDictError(Exception):
    pass


def _to_python(value):
    raw = value.get("raw", "")
    country = value.get("country", "")
    country_code = value.get("country_code", "")
    state = value.get("state", "")
    state_code = value.get("state_code", "")
    locality = value.get("locality", "")
    sublocality = value.get("sublocality", "")
    postal_town = value.get("postal_town", "")
    postal_code = value.get("postal_code", "")
    street_number = value.get("street_number", "")
    route = value.get("route", "")
    formatted = value.get("formatted", "")
    latitude = value.get("latitude", None)
    longitude = value.get("longitude", None)

    # If there is no value (empty raw) then return None.
    if not raw:
        return None

    # Fix issue with NYC boroughs (https://code.google.com/p/gmaps-api-issues/issues/detail?id=635)
    if not locality and sublocality:
        locality = sublocality

    # Fix issue with UK addresses with no locality
    # (https://github.com/furious-luke/django-address/issues/114)
    if not locality and postal_town:
        locality = postal_town

    # If we have an inconsistent set of value bail out now.
    if (country or state or locality) and not (country and state and locality):
        raise InconsistentDictError

    # Handle the country.
    try:
        country_obj = Country.objects.get(name=country)
    except Country.DoesNotExist:
        if country:
            if len(country_code) > Country._meta.get_field("code").max_length:
                if country_code != country:
                    raise ValueError("Invalid country code (too long): %s" % country_code)
                country_code = ""
            country_obj = Country.objects.create(name=country, code=country_code)
        else:
            country_obj = None

    # Handle the state.
    try:
        state_obj = State.objects.get(name=state, country=country_obj)
    except State.DoesNotExist:
        if state:
            if len(state_code) > State._meta.get_field("code").max_length:
                if state_code != state:
                    raise ValueError("Invalid state code (too long): %s" % state_code)
                state_code = ""
            state_obj = State.objects.create(name=state, code=state_code, country=country_obj)
        else:
            state_obj = None

    # Handle the locality.
    try:
        locality_obj = Locality.objects.get(name=locality, postal_code=postal_code, state=state_obj)
    except Locality.DoesNotExist:
        if locality:
            locality_obj = Locality.objects.create(name=locality, postal_code=postal_code, state=state_obj)
        else:
            locality_obj = None

    # Handle the address.
    try:
        if not (street_number or route or locality):
            address_obj = Address.objects.get(raw=raw)
        else:
            address_obj = Address.objects.get(street_number=street_number, route=route, locality=locality_obj)
    except Address.DoesNotExist:
        address_obj = Address(
            street_number=street_number,
            route=route,
            raw=raw,
            locality=locality_obj,
            formatted=formatted,
            latitude=latitude,
            longitude=longitude,
        )

        # If "formatted" is empty try to construct it from other values.
        if not address_obj.formatted:
            address_obj.formatted = str(address_obj)

        # Need to save.
        address_obj.save()

    # Done.
    return address_obj


##
# Convert a dictionary to an address.
##


def to_python(value):

    # Keep `None`s.
    if value is None:
        return None

    # Is it already an address object?
    if isinstance(value, Address):
        return value

    # If we have an integer, assume it is a model primary key.
    elif isinstance(value, int):
        return value

    # A string is considered a raw value.
    elif isinstance(value, str):
        obj = Address(raw=value)
        obj.save()
        return obj

    # A dictionary of named address components.
    elif isinstance(value, dict):

        # Attempt a conversion.
        try:
            return _to_python(value)
        except InconsistentDictError:
            return Address.objects.create(raw=value["raw"])

    # Not in any of the formats I recognise.
    raise ValidationError("Invalid address value.")


##
# A country.
##


class Country(models.Model):
    name = models.CharField(max_length=40, unique=True, blank=True)
    code = models.CharField(max_length=2, blank=True)  # not unique as there are duplicates (IT)
     #最高院
    court = models.CharField(max_length=165, blank=True)
    courtAddress = models.CharField(max_length=165, blank=True)
    courtPhoneNumber =models.CharField(max_length=15, blank=True)
    courtLatitude = models.FloatField(blank=True, null=True)
    courtLongitude = models.FloatField(blank=True, null=True)
    courtWebsite = models.CharField(max_length=165, blank=True)

    class Meta:
        verbose_name_plural = "Countries"
        ordering = ("name",)

    def __str__(self):
        return "%s" % (self.name or self.code)


##
# A CountryStat. 
##


class CountryStat(models.Model):
     
    year = models.IntegerField(default=0, editable=True)
    lprDate = models.DateField(null=True,editable=True)
    #全国城镇居民人均可支配收入
    avgCityPerson = models.FloatField(default=0, editable=True)
    #全国农村居民人均可支配收入
    avgCountryPerson = models.FloatField(default=0, editable=True)
    #lpr 
    oneYearLpr = models.FloatField(default=0, editable=True)
    twoYearLpr = models.FloatField(default=0, editable=True)
    threeYearLpr = models.FloatField(default=0, editable=True)
    fourYearLpr = models.FloatField(default=0, editable=True)
    fiveYearLpr = models.FloatField(default=0, editable=True)
    
    #source
    source = models.CharField(max_length=255, blank=True)

    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="countryStat")
   

    class Meta:
        #unique_together = ("country", "year")
        ordering = ("country", "year")

    def __str__(self):
        txt = self.to_str()
        country = "%s" % self.country
        if country and txt:
            txt += ", "
        txt += country
        return txt

    def to_str(self):
        return "%s" % (self.country and self.year)

##
# A state. Google refers to this as `administration_level_1`.
##


class State(models.Model):
    name = models.CharField(max_length=165, blank=True)
    code = models.CharField(max_length=8, blank=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="states")

    #省法院
    stateCourt = models.CharField(max_length=165, blank=True)
    stateCourtAddress = models.CharField(max_length=165, blank=True)
    courtPhoneNumber =models.CharField(max_length=15, blank=True)
    courtLatitude = models.FloatField(blank=True, null=True)
    courtLongitude = models.FloatField(blank=True, null=True)
    courtWebsite = models.CharField(max_length=165, blank=True)

    class Meta:
        unique_together = ("name", "country")
        ordering = ("country", "name")

    def __str__(self):
        txt = self.to_str()
        country = "%s" % self.country
        if country and txt:
            txt += ", "
        txt += country
        return txt

    def to_str(self):
        return "%s" % (self.name or self.code)


##
# A locality (suburb).
##

class StateStat(models.Model):
    year = models.IntegerField(default=0, editable=False)
    #职工平均工资
    avgEmpSalary = models.FloatField(default=0, editable=False)
    #最低工资
    lowEmpSalary = models.FloatField(default=0, editable=False)
    #source
    source = models.CharField(max_length=255, blank=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="stateStat")
    

    class Meta:
        #unique_together = ("country", "year")
        ordering = ("state", "year")

    def __str__(self):
        txt = self.to_str()
        state = "%s" % self.state
        if state and txt:
            txt += ", "
        txt += state
        return txt

    def to_str(self):
        return "%s" % (self.state and self.year)

class Locality(models.Model):
    name = models.CharField(max_length=165, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="localities")
    #市法院
    localCourt = models.CharField(max_length=165, blank=True)
    localCourtAddress = models.CharField(max_length=165, blank=True)
    courtPhoneNumber =models.CharField(max_length=15, blank=True)
    courtLatitude = models.FloatField(blank=True, null=True)
    courtLongitude = models.FloatField(blank=True, null=True)
    courtWebsite = models.CharField(max_length=165, blank=True)

    class Meta:
        verbose_name_plural = "Localities"
        unique_together = ("name", "postal_code", "state")
        ordering = ("state", "name")

    def __str__(self):
        txt = "%s" % self.name
        state = self.state.to_str() if self.state else ""
        if txt and state:
            txt += ", "
        txt += state
        if self.postal_code:
            txt += " %s" % self.postal_code
        cntry = "%s" % (self.state.country if self.state and self.state.country else "")
        if cntry:
            txt += ", %s" % cntry
        return txt


class LocalityStat(models.Model):
    year = models.IntegerField(default=0, editable=False)
    #职工平均工资
    avgEmpSalary = models.FloatField(default=0, editable=False)
    #最低工资
    lowEmpSalary = models.FloatField(default=0, editable=False)
    #source
    source = models.CharField(max_length=255, blank=True)
    locality = models.ForeignKey(Locality, on_delete=models.CASCADE, related_name="localityStat")
    

    class Meta:
        #unique_together = ("country", "year")
        ordering = ("locality", "year")

    def __str__(self):
        txt = self.to_str()
        locality = "%s" % self.locality
        if locality and txt:
            txt += ", "
        txt += locality
        return txt

    def to_str(self):
        return "%s" % (self.locality and self.year)

##
# An address. If for any reason we are unable to find a matching
# decomposed address we will store the raw address string in `raw`.
##


class Address(models.Model):
    street_number = models.CharField(max_length=20, blank=True)
    route = models.CharField(max_length=100, blank=True)
    locality = models.ForeignKey(
        Locality,
        on_delete=models.CASCADE,
        related_name="addresses",
        blank=True,
        null=True,
    )
    raw = models.CharField(max_length=200)
    formatted = models.CharField(max_length=200, blank=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    

    #县法院
    countyCourt = models.CharField(max_length=165, blank=True)
    countyCourtAddress = models.CharField(max_length=165, blank=True)
    courtPhoneNumber =models.CharField(max_length=15, blank=True)
    courtLatitude = models.FloatField(blank=True, null=True)
    courtLongitude = models.FloatField(blank=True, null=True)
    countyCourtWebsite = models.CharField(max_length=165, blank=True)

    #劳动争议仲裁委
    countyAitration = models.CharField(max_length=165, blank=True)
    countyAitrationAddress = models.CharField(max_length=165, blank=True)
    aitrationPhoneNumber =models.CharField(max_length=15, blank=True)
    aitrationLatitude = models.FloatField(blank=True, null=True)
    aitrationLongitude = models.FloatField(blank=True, null=True)
    aitrationWebsite = models.CharField(max_length=165, blank=True)

    class Meta:
        verbose_name_plural = "Addresses"
        ordering = ("locality", "route", "street_number")

    def __str__(self):
        if self.formatted != "":
            txt = "%s" % self.formatted
        elif self.locality:
            txt = ""
            if self.street_number:
                txt = "%s" % self.street_number
            if self.route:
                if txt:
                    txt += " %s" % self.route
            locality = "%s" % self.locality
            if txt and locality:
                txt += ", "
            txt += locality
        else:
            txt = "%s" % self.raw
        return txt

    def clean(self):
        if not self.raw:
            raise ValidationError("Addresses may not have a blank `raw` field.")

    def as_dict(self):
        ad = dict(
            street_number=self.street_number,
            route=self.route,
            raw=self.raw,
            formatted=self.formatted,
            latitude=self.latitude if self.latitude else "",
            longitude=self.longitude if self.longitude else "",
        )
        if self.locality:
            ad["locality"] = self.locality.name
            ad["postal_code"] = self.locality.postal_code
            if self.locality.state:
                ad["state"] = self.locality.state.name
                ad["state_code"] = self.locality.state.code
                if self.locality.state.country:
                    ad["country"] = self.locality.state.country.name
                    ad["country_code"] = self.locality.state.country.code
        return ad


class AddressDescriptor(ForwardManyToOneDescriptor):
    def __set__(self, inst, value):
        super(AddressDescriptor, self).__set__(inst, to_python(value))


##
# A field for addresses in other models.
##


class AddressField(models.ForeignKey):
    description = "An address"

    def __init__(self, *args, **kwargs):
        kwargs["to"] = "address.Address"
        # The address should be set to null when deleted if the relationship could be null
        default_on_delete = models.SET_NULL if kwargs.get("null", False) else models.CASCADE
        kwargs["on_delete"] = kwargs.get("on_delete", default_on_delete)
        super(AddressField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name, virtual_only=False):
        from address.compat import compat_contribute_to_class

        compat_contribute_to_class(self, cls, name, virtual_only)

        setattr(cls, self.name, AddressDescriptor(self))

    def formfield(self, **kwargs):
        from .forms import AddressField as AddressFormField

        defaults = dict(form_class=AddressFormField)
        defaults.update(kwargs)
        return super(AddressField, self).formfield(**defaults)

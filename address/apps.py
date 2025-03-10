from django.apps import AppConfig


class AddressConfig(AppConfig):
    """
    Define config for the member app so that we can hook in signals.
    """

    name = "address"
    default_auto_field = "django.db.models.AutoField"

# Generated by Django 3.0.6 on 2020-06-28 19:20

import address.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("address", "0002_auto_20160213_1726"),
        ("person", "0002_auto_20200628_1720"),
    ]

    operations = [
        migrations.AddField(
            model_name="person",
            name="first_name",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name="person",
            name="address",
            field=address.models.AddressField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="address.Address",
            ),
        ),
    ]

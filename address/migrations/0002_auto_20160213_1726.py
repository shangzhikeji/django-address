# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("address", "0001_initial"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="locality",
            unique_together=set([("name", "postal_code", "state")]),
        ),
    ]

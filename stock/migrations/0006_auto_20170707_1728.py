# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-07 17:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0005_auto_20170707_1707'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stock',
            name='inflight',
            field=models.IntegerField(default=0, null=True),
        ),
    ]

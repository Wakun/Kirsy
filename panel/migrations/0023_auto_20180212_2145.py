# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-02-12 20:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('panel', '0022_auto_20180201_2314'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalproduct',
            name='owner_name',
            field=models.CharField(default=1, max_length=255, verbose_name='Nazwa grupy: '),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='product',
            name='owner_name',
            field=models.CharField(default=2, max_length=255, verbose_name='Nazwa grupy: '),
            preserve_default=False,
        ),
    ]

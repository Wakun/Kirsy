# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-02-01 22:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('panel', '0021_auto_20180124_2139'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalproduct',
            name='temporary_quantity',
            field=models.IntegerField(default=0, verbose_name='Tymczasowa ilość'),
        ),
        migrations.AddField(
            model_name='product',
            name='temporary_quantity',
            field=models.IntegerField(default=0, verbose_name='Tymczasowa ilość'),
        ),
    ]

# Generated by Django 2.0.2 on 2018-05-24 20:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('panel', '0023_auto_20180212_2145'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalproduct',
            name='product_status',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='product',
            name='product_status',
            field=models.BooleanField(default=True),
        ),
    ]

# Generated by Django 2.1.7 on 2019-05-07 06:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emails', '0007_lockedemail'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lockedemail',
            name='locked',
            field=models.BooleanField(default=False),
        ),
    ]

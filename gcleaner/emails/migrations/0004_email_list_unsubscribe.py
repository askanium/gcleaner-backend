# Generated by Django 2.1.7 on 2019-04-03 19:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emails', '0003_latestemail'),
    ]

    operations = [
        migrations.AddField(
            model_name='email',
            name='list_unsubscribe',
            field=models.TextField(blank=True),
        ),
    ]

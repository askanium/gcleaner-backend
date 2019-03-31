# Generated by Django 2.1.7 on 2019-03-30 11:46

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('emails', '0002_auto_20190326_2035'),
    ]

    operations = [
        migrations.CreateModel(
            name='LatestEmail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='latest_email', to='emails.Email')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='latest_email', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

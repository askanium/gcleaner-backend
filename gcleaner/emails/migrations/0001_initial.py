# Generated by Django 2.1.7 on 2019-03-26 20:35

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Email',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('google_id', models.CharField(max_length=16, unique=True)),
                ('thread_id', models.CharField(max_length=16, unique=True)),
                ('subject', models.TextField()),
                ('snippet', models.TextField()),
                ('sender', models.CharField(max_length=254)),
                ('receiver', models.CharField(max_length=254)),
                ('delivered_to', models.CharField(max_length=254)),
                ('starred', models.BooleanField(default=False)),
                ('important', models.BooleanField(default=False)),
                ('date', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Label',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('google_id', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
            ],
        ),
    ]

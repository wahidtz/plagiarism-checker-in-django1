# Generated by Django 3.2 on 2021-07-15 07:06

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('blog', '0002_auto_20210715_0135'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='document',
            name='description',
        ),
    ]
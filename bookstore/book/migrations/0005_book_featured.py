# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-19 19:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('book', '0004_book_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='featured',
            field=models.BooleanField(default=False),
        ),
    ]

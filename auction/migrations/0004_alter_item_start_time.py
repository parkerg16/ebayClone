# Generated by Django 5.0.6 on 2024-06-27 01:07

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auction', '0003_alter_item_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='start_time',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False),
        ),
    ]

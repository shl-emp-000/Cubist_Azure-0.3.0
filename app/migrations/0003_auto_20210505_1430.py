# Generated by Django 3.1.8 on 2021-05-05 14:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_auto_20210504_0858'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='device',
            options={'ordering': ['-created']},
        ),
        migrations.AlterModelOptions(
            name='firmware',
            options={'ordering': ['-fw_version']},
        ),
        migrations.AlterModelOptions(
            name='history',
            options={'ordering': ['-fw_update_started'], 'verbose_name_plural': 'History'},
        ),
    ]

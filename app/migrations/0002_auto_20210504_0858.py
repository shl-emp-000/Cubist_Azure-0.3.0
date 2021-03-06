# Generated by Django 3.1.8 on 2021-05-04 08:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='device',
            name='hardware_revision',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='HW rev.'),
        ),
        migrations.AlterField(
            model_name='device',
            name='model_number',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Model#'),
        ),
        migrations.AlterField(
            model_name='device',
            name='software_revision',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='SW rev.'),
        ),
        migrations.AlterField(
            model_name='history',
            name='hardware_revision',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='HW rev.'),
        ),
        migrations.AlterField(
            model_name='history',
            name='model_number',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Model#'),
        ),
        migrations.AlterField(
            model_name='history',
            name='software_revision',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='SW rev.'),
        ),
    ]

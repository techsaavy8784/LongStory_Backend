# Generated by Django 4.2.5 on 2023-10-19 14:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0006_alter_metadata_field'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventory',
            name='currency',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]

# Generated by Django 4.2.5 on 2023-10-12 14:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_alter_user_avatar_url_alter_user_username'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='approved_status',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]

# Generated by Django 3.2.6 on 2021-08-15 16:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('watchlist', '0002_auto_20210815_2047'),
    ]

    operations = [
        migrations.RenameField(
            model_name='stockbalancesheet',
            old_name='otherCurrentLiabilites',
            new_name='otherCurrentLiabilities',
        ),
        migrations.RenameField(
            model_name='stockbalancesheet',
            old_name='totalLiabilites',
            new_name='totalLiabilities',
        ),
    ]

# Generated by Django 3.2.4 on 2022-01-09 09:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('watchlist', '0007_watchlist_backtest_result'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='watchlist',
            name='backtest_result',
        ),
        migrations.AddField(
            model_name='stock',
            name='backtest_result',
            field=models.TextField(blank=True, null=True),
        ),
    ]

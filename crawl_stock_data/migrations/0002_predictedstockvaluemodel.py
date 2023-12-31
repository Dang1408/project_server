# Generated by Django 4.2.3 on 2023-09-02 07:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crawl_stock_data', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PredictedStockValueModel',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, unique=True)),
                ('symbol', models.CharField(max_length=30)),
                ('created_at', models.DecimalField(decimal_places=0, max_digits=100)),
                ('predicted_date_at', models.CharField(max_length=30)),
                ('predicted_value', models.DecimalField(decimal_places=5, max_digits=20)),
                ('predicted_model', models.CharField(max_length=100)),
                ('is_success', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name_plural': 'predicted_stock_value',
                'db_table': 'predicted_stock_value',
                'ordering': ['-created_at'],
            },
        ),
    ]

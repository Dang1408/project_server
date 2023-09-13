# Generated by Django 4.2.3 on 2023-08-29 15:23

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='StockData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('symbol', models.CharField(max_length=30)),
                ('created_at', models.DecimalField(decimal_places=0, max_digits=19)),
                ('currency', models.CharField(max_length=30)),
                ('date_time', models.CharField(max_length=100)),
                ('timestamp', models.DecimalField(decimal_places=0, max_digits=19)),
                ('open', models.DecimalField(decimal_places=2, max_digits=16)),
                ('high', models.DecimalField(decimal_places=2, max_digits=16)),
                ('low', models.DecimalField(decimal_places=2, max_digits=16)),
                ('volume', models.DecimalField(decimal_places=0, max_digits=19)),
                ('close', models.DecimalField(decimal_places=2, max_digits=16)),
                ('type_profile', models.CharField(default='1', max_length=10)),
                ('adj_close', models.DecimalField(decimal_places=2, max_digits=16)),
            ],
            options={
                'verbose_name_plural': 'stock_data',
                'db_table': 'stock_data',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='TrainingLogModel',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, unique=True)),
                ('symbol', models.CharField(max_length=30)),
                ('created_at', models.DecimalField(decimal_places=0, max_digits=100)),
                ('model', models.CharField(max_length=100)),
                ('training_date_at', models.CharField(max_length=30)),
                ('is_success', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name_plural': 'training_log',
                'db_table': 'training_log',
                'ordering': ['-created_at'],
            },
        ),
    ]
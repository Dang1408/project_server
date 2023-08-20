import uuid

from django.db import models


# Create your models here.
class StockData(models.Model):
    symbol_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    symbol = models.CharField(max_length=30)
    created_at = models.DecimalField(max_digits=19, decimal_places=0)
    currency = models.CharField(max_length=30)
    date_time = models.CharField(max_length=100)
    timestamp = models.DecimalField(max_digits=19, decimal_places=0)
    open = models.DecimalField(max_digits=16, decimal_places=2)
    high = models.DecimalField(max_digits=16, decimal_places=2)
    low = models.DecimalField(max_digits=16, decimal_places=2)
    volume = models.DecimalField(max_digits=19, decimal_places=0)
    close = models.DecimalField(max_digits=16, decimal_places=2)
    type_profile = models.CharField(max_length=10, default='1', null=False)
    adj_close = models.DecimalField(max_digits=16, decimal_places=2)

    def __init__(self, *args, **kwargs):
        # Call the superclass constructor to initialize the model instance
        super(StockData, self).__init__(*args, **kwargs)

        # Set the default value for the type_profile field
        self.type_profile = '1'

    def __str__(self, *args, **kwargs):
        return self.symbol

    class Meta:
        app_label = 'crawl_stock_data'
        db_table = 'stock_data'
        verbose_name_plural = 'stock_data'
        ordering = ['-created_at']

    def to_dict(self):
        return {
            'date': self.date_time,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume
        }
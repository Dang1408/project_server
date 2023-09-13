from django.db import models


class PredictedStockValueModel(models.Model):
    """
    Model for storing predicted stock values
    """
    id = models.AutoField(primary_key=True, unique=True, null=False)
    symbol = models.CharField(max_length=30)
    created_at = models.DecimalField(max_digits=100, decimal_places=0)
    predicted_date_at = models.CharField(max_length=30)
    predicted_value = models.DecimalField(max_digits=20, decimal_places=5)
    predicted_model = models.CharField(max_length=100)
    is_success = models.BooleanField(default=False)
    predicted_date_at_in_timestamp = models.DecimalField(max_digits=100, decimal_places=0)

    def __str__(self, *args, **kwargs):
        return self.symbol

    class Meta:
        app_label = 'crawl_stock_data'
        db_table = 'predicted_stock_value'
        verbose_name_plural = 'predicted_stock_value'
        ordering = ['-created_at']

    def to_dict(self):
        return {
            'symbol': self.symbol,
            'created_at': self.created_at,
            'predicted_date_at': self.predicted_date_at,
            'predicted_value': self.predicted_value,
            'predicted_model': self.predicted_model,
            'is_success': self.is_success
        }

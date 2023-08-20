from django.db import models


class TrainingLogModel(models.Model):
    id = models.AutoField(primary_key=True)
    symbol = models.CharField(max_length=30)
    created_at = models.DecimalField(max_digits=19, decimal_places=0)
    model = models.CharField(max_length=100)
    training_date_at = models.CharField(max_length=100)
    is_success = models.BooleanField(default=False)

    def __str__(self, *args, **kwargs):
        return self.symbol

    class Meta:
        app_label = 'crawl_stock_data'
        db_table = 'training_log'
        verbose_name_plural = 'training_log'
        ordering = ['-created_at']

    def to_dict(self):
        return {
            'symbol': self.symbol,
            'created_at': self.created_at,
            'training_date_at': self.training_date_at,
            'is_success': self.is_success,
            'model': self.model
        }

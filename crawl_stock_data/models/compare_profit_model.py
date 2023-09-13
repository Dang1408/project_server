from django.db import models


class CompareProfitResultModel(models.Model):
    id = models.AutoField(primary_key=True, unique=True, null=False)
    symbol = models.CharField(max_length=30)
    created_at = models.DecimalField(max_digits=100, decimal_places=0)
    actual_profit = models.DecimalField(max_digits=20, decimal_places=5)
    predicted_profit = models.DecimalField(max_digits=20, decimal_places=5)

    def __str__(self, *args, **kwargs):
        return self.symbol

    class Meta:
        app_label = 'crawl_stock_data'
        db_table = 'compare_profit_result'
        verbose_name_plural = 'compare_profit_result'
        ordering = ['-created_at']

    def to_dict(self):
        return {
            'symbol': self.symbol,
            'created_at': self.created_at,
            'actual_profit': self.actual_profit,
            'predicted_profit': self.predicted_profit
        }

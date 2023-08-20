from django.apps import AppConfig


class CrawlStockDataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crawl_stock_data'

    def ready(self):
        from .sheduler import setup_scheduler
        # Call the setup_scheduler function here
        setup_scheduler()

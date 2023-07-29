from django.urls import path
from . import views

urlpatterns = [
    path('api/stock/<str:symbol>/', views.get_stock_value, name='get_stock_value'),
    path('api/stock', views.get_stock_value_by_date, name='get_stock_value_by_date'),
    path('api/stock/drawl-chart', views.get_stock_value_by_date_drawl_chart, name='get_stock_value_by_date_drawl_chart'),
    path('api/stock/crawl-stock-data', views.crawl_stock_data, name='crawl_stock_data'),
    path('api/model/training_SARIMAX', views.predict_stock_value_by_the_number_date, name='training_model'),
    path('api/model/predict-next-date', views.predict_stock_value_on_the_next_date, name='predict_stock_value_next_date'),
    path('', views.home_view, name='home_view'),
]

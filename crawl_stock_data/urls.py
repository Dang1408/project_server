from django.urls import path
from crawl_stock_data.views import general_view, nyse_view, vnindex_view

urlpatterns = [
    path('api/upload-vn-stock', vnindex_view.upload_vn_stock_file_csv, name='upload_vn_stock_file_csv'),
    path('api/compare-buy-sell-signal', nyse_view.compare_buy_sell, name='compare_buy_sell'),
    path('api/stock/drawl-chart', general_view.get_stock_value_by_date_drawl_chart,
         name='get_stock_value_by_date_drawl_chart'),
    path('api/stock/crawl-stock-data', nyse_view.crawl_stock_data, name='crawl_stock_data'),
    path('api/model/predict-next-date', general_view.predict_stock_value_on_the_next_date,
         name='predict_stock_value_next_date'),
    path('api/test', general_view.test_training_model, name='test_training_model'),
    path('api/get-stock-symbol', nyse_view.get_stock_symbols, name='get_stock_symbol'),
    path('', nyse_view.nyse_view, name='nyse_view'),
    path('stock-vietnam', vnindex_view.vn_stock_view, name='vn_stock_view'),
]

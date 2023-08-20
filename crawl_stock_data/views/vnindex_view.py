import json
import os

import pytz
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from crawl_stock_data.dao.stock_data_dao import check_exist_stock_data, delete_stock_data, insert
from crawl_stock_data.service.handle_data_service import HandleStockDataService
from crawl_stock_data.service.process_data_service import ProcessDataService
from crawl_stock_data.training.SVM import SVM_model


def vn_stock_view(request):
    return render(request, 'vn-stock.html')


@csrf_exempt
@require_POST
def upload_vn_stock_file_csv(request):
    # try:
    csv_file = request.FILES['file']
    if not csv_file.name.endswith('.csv'):
        return JsonResponse({'success': False, 'error': 'File is not CSV type'})

    # if file is too large, return
    if csv_file.multiple_chunks():
        return JsonResponse({'success': False, 'error': 'File is too large'})

    process_data_service = ProcessDataService(None)
    vn_stock_data, stock_name = process_data_service.process_VNINDEX_stock_data(csv_file)

    # save the data into database
    handle_data_service = HandleStockDataService(vn_stock_data)
    vn_stock_model = handle_data_service.parse_df_to_stock_data_model(stock_name)

    if check_exist_stock_data(stock_name):
        delete_stock_data(stock_name)

    for data in vn_stock_model:
        insert(data)

    # predict and save file

    path = ('/mnt/learning/last_project/app/server/stock_server/'
            'crawl_stock_data/training/checkpoint/online_learning_model/'
            'svm/SVM_{}_13-23.pkl'.format(stock_name))

    SVM = SVM_model(symbol=stock_name, path=path)

    if SVM.check_file_existence():
        os.remove(path)

    SVM.training()

    response_data = []

    for index, row in vn_stock_data.iterrows():
        utc_timezone = pytz.timezone('UTC')
        date_object_utc = utc_timezone.localize(index)
        temp_dic = {
            "date": int(date_object_utc.timestamp()) * 1000,
            "open": row['open'],
            "high": row['high'],
            "low": row['low'],
            "close": row['close'],
            "volume": row['volume'],
        }

        response_data.append(temp_dic)

    return JsonResponse({'success': True, 'data': {"symbol": stock_name, "stock_data": response_data}})

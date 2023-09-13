import json


def read_file_export_list_of_symbol():
    with open("/mnt/learning/last_project/app/server/"
              "stock_server/crawl_stock_data/config/symbols.json", "r") as file:
        data = json.load(file)

    return data["general_symbol"]

from django.db import connection

from crawl_stock_data.models.traning_log_model import TrainingLogModel


# select

def get_training_log(symbol):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, symbol, created_at, model, training_date_at, is_success FROM training_log WHERE symbol = %s",
            [symbol.upper()]
        )
        data = cursor.fetchall()

    # Create a list to store the model class objects
    training_log_list = []

    # Loop through the fetched data and create model class objects
    for row in data:
        training_log_obj = TrainingLogModel(
            id=row[0],
            symbol=row[1],
            created_at=row[2],
            model=row[3],
            training_date_at=row[4],
            is_success=row[5],
        )
        training_log_list.append(training_log_obj)

    return training_log_list


def get_training_log_by_date(symbol, model, date):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, symbol, created_at, model, training_date_at, is_success "
            "FROM training_log "
            "WHERE symbol = %s and model = %s AND training_date_at = %s",
            [symbol.upper(), model, date]
        )
        data = cursor.fetchall()

    # Create a list to store the model class objects
    training_log_list = []

    # Loop through the fetched data and create model class objects
    for row in data:
        training_log_obj = TrainingLogModel(
            id=row[0],
            symbol=row[1],
            created_at=row[2],
            model=row[3],
            training_date_at=row[4],
            is_success=row[5],
        )
        training_log_list.append(training_log_obj)

    return training_log_list
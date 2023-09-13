from datetime import datetime, timedelta, timezone

import pytz


def get_date_now():
    return str(datetime.now().strftime("%Y-%m-%d"))


def get_the_time_of_n_week_ago(the_number_of_week=1):
    current_date = datetime.now()
    before_date = current_date - timedelta(days=7*the_number_of_week)

    return str(before_date.strftime("%Y-%m-%d")), str(current_date.strftime("%Y-%m-%d"))


def convert_to_timezone(timestamp):
    # convert the timestamp to My timezone timestamp
    time_zone = pytz.timezone('Asia/Ho_Chi_Minh')
    # convert the timestamp to UTC timestamp
    timestamp = timestamp / 1000
    timestamp = datetime.fromtimestamp(int(timestamp))
    timestamp = timestamp.astimezone(time_zone)
    timestamp = timestamp.replace(tzinfo=None)
    timestamp = int(timestamp.timestamp()) * 1000

    return timestamp


def get_the_list_of_date_in_one_week_age():
    the_list_of_date = []
    current_date = datetime.now()

    time_zone = pytz.timezone('Asia/Ho_Chi_Minh')

    for i in range(14):
        before_date = current_date - timedelta(days=i)

        date_to_check = time_zone.localize(before_date)

        if date_to_check.weekday() != 5 and date_to_check.weekday() != 6:
            the_list_of_date.append(str(before_date.strftime("%Y-%m-%d")))

    return the_list_of_date


def get_the_list_of_date_in_n_week_age(the_number_of_week=1):
    the_list_of_date = []
    current_date = datetime.now()

    time_zone = pytz.timezone('Asia/Ho_Chi_Minh')

    for i in range(7 * the_number_of_week):
        before_date = current_date - timedelta(days=i)

        date_to_check = time_zone.localize(before_date)

        if (date_to_check.weekday() != 5
                and date_to_check.weekday() != 6
                and str(before_date.strftime("%Y-%m-%d")) != '2023-09-04'):
            the_list_of_date.append(str(before_date.strftime("%Y-%m-%d")))

    return the_list_of_date


def get_the_next_date(date, market="NYSE"):
    if market == "NYSE":
        time_zone = pytz.timezone('America/New_York')
    else:
        time_zone = pytz.timezone('Asia/Ho_Chi_Minh')

    if date is None:
        date = datetime.now()

    date_time = datetime.strptime(date, '%Y-%m-%d')
    next_date = date_time + timedelta(days=1)
    date_to_check = time_zone.localize(next_date)

    if date_to_check.weekday() == 5:
        next_date = next_date + timedelta(days=2)
    elif date_to_check.weekday() == 6:
        next_date = next_date + timedelta(days=1)

    return str(next_date.strftime("%Y-%m-%d"))


def convert_to_GMT_timestamp(date):
    date_time = datetime.strptime(date, '%Y-%m-%d')
    date_time = date_time.replace(tzinfo=timezone.utc)
    date_time = int(date_time.timestamp()) * 1000

    return date_time


def get_the_last_one_and_two_day(date_time: datetime):
    last_two_day = date_time - timedelta(days=2)
    last_one_day = date_time - timedelta(days=1)

    time_zone = pytz.timezone('Asia/Ho_Chi_Minh')
    date_to_check_last_one_date = time_zone.localize(last_one_day)
    date_to_check_last_two_date = time_zone.localize(last_two_day)

    if date_to_check_last_one_date.weekday() == 6 and date_to_check_last_two_date.weekday() == 5:
        last_one_day = last_one_day - timedelta(days=2)
        last_two_day = last_two_day - timedelta(days=2)
    elif date_to_check_last_one_date.weekday() == 0 and date_to_check_last_two_date.weekday() == 6:
        last_two_day = last_two_day - timedelta(days=2)

    if str(last_one_day.strftime("%Y-%m-%d")) == '2023-09-04':
        last_one_day = last_one_day - timedelta(days=3)
        last_two_day = last_two_day - timedelta(days=1)
    elif str(last_two_day.strftime("%Y-%m-%d")) == '2023-09-04':
        last_two_day = last_two_day - timedelta(days=3)

    last_two_day = str(last_two_day.strftime("%Y-%m-%d"))
    last_one_day = str(last_one_day.strftime("%Y-%m-%d"))

    return last_one_day, last_two_day

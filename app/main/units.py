import datetime

# convert temperature between F and C


def convert_temp(temp: float, units: str):
    converted_temp = temp
    if units.upper() == 'F':
        converted_temp = (temp * 9 / 5) + 32  # convert celcius to fahrenheit
    else:
        converted_temp = (temp - 32) * 5 / 9  # convert fahrenheit to celcius

    return round(converted_temp, 2)


def epoch_time(date1):
    return (date1 - datetime.datetime(1970, 1, 1)).total_seconds() * 1000


def excel_date(date1):
    temp = datetime.datetime(1899, 12, 30)    # Note, not 31st Dec but 30th!
    delta = date1 - temp
    return float(delta.days) + (float(delta.seconds) / 86400)
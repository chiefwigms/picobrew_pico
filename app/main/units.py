# convert temperature between F and C
def convert_temp(temp: float, units: str):
    converted_temp = temp
    if units.upper() == 'F':
        converted_temp = (temp * 9/5) + 32  # convert celcius to fahrenheit
    else:
        converted_temp = (temp - 32) * 5/9  # convert fahrenheit to celcius

    return round(converted_temp, 2)
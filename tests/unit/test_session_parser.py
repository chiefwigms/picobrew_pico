import datetime
from dateutil import tz

from app.main.session_parser import epoch_millis_converter


def test_epoch_millis_converter():
    """Verify that epoch convertion works"""

    local_datetime = epoch_millis_converter(0)
    epoch_datetime_utc = datetime.datetime(1970, 1, 1).replace(tzinfo=tz.tzutc())
    assert local_datetime == epoch_datetime_utc.astimezone(tz.tzlocal())

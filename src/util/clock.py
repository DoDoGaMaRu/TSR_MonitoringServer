from time import time, localtime, strftime


def get_time() -> str:
    return strftime('%H:%M:%S', localtime(time()))


def get_hour() -> str:
    return strftime('%H', localtime(time()))


def get_min() -> str:
    return strftime('%M', localtime(time()))


def get_date() -> str:
    return strftime('%Y%m%d', localtime(time()))


class TimeEvent:
    def __init__(self):
        self._prev_date = get_date()
        self._prev_hour = get_hour()
        self._prev_min = get_min()

    def is_min_change(self):
        is_min_changed = self._prev_min != get_min()
        if is_min_changed:
            self._prev_min = get_min()
        return is_min_changed

    def is_hour_change(self):
        is_hour_changed = self._prev_hour != get_hour()
        if is_hour_changed:
            self._prev_hour = get_hour()
        return is_hour_changed

    def is_day_change(self):
        is_day_changed = self._prev_date != get_date()
        if is_day_changed:
            self._prev_date = get_date()
        return is_day_changed

import datetime

def now():
    return datetime.datetime.utcnow()

def format_datetime(dt):
    return dt.strftime('%Y-%m-%d %H:%M') if dt else ''

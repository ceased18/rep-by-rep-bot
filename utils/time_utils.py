import pytz
from datetime import datetime

def get_est_time():
    """Get current time in EST"""
    est = pytz.timezone('America/New_York')
    return datetime.now(est)

def is_check_in_time():
    """Check if it's time for daily check-in (8 PM EST)"""
    current_time = get_est_time()
    return current_time.hour == 20 and current_time.minute == 0

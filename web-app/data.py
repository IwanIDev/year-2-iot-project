"""
Gets and interprets thingsboard data to be displayed
"""
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from flask_login import current_user
from telemetry.Telemetry import Telemetry

TYPES = ["CARDBOARD-PAPER", "FOOD", "GENERAL WASTE", "GLASS", "HARD PLASTIC", "METAL", "SOFT PLASTIC"]

def get_user_telemetry():
    """
    Get all telemetry data for the current logged-in user
    Returns list of dicts with 'ts' and 'value' keys for consistency with existing code
    """
    if not current_user.is_authenticated:
        return []
    
    items = Telemetry.query.filter_by(deviceId=current_user.device_id).all()
    data = []
    for item in items:
        data.append({
            "ts": item.timestamp.timestamp(),
            "value": item.wasteType
        })
    return data

def sort(data):
    """
        Merge sorts the data based on timestamp (earliest first)

        Parameters
            data: list of dicts containing timestamp 'ts' and category 'value'
        
        Returns
            list of dicts containing timestamp 'ts' and category 'value', ordered by ascending timestamp
    """
    if len(data) <= 1:
        return data
    
    mid = len(data) // 2
    left = data[:mid]
    right = data[mid:]

    sorted_left = sort(left)
    sorted_right = sort(right)

    return merge(sorted_left, sorted_right)

def merge(left, right):
    """
        Helper function for 'sort(data)'.
        Merges two sorted lists in the correct order.

        Parameters:
            left:   sorted list of dicts containing timestamp 'ts' and category 'value'
            right:  sorted list of dicts containing timestamp 'ts' and category 'value'
        
        Returns
            sorted list of dicts containing timestamp 'ts' and category 'value'
    """
    output = []
    i = j = 0

    while i < len(left) and j < len(right):
        if left[i]["ts"] < right[j]["ts"]:
            output.append(left[i])
            i += 1
        else:
            output.append(right[j])
            j += 1
    
    output.extend(left[i:])
    output.extend(right[j:])

    return output

def results_in_time(data,time="all"):
    """
    Gets all categories in a given timeframe

    Parameters:
        data:   list of dicts containing timestamp 'ts' and category 'value'
        time:   string containing one of:
            7days, 14days, month, 6months, year, all | None = "all"
    
    Returns:
        list:   list of dicts " (only items scanned within the timeframe)
    """
    if time == "all":
        return data
    
    now = datetime.now()
    DT = {
        "7days":datetime.timestamp(now-timedelta(weeks=1)),
        "14days":datetime.timestamp(now-timedelta(weeks=2)),
        "month":datetime.timestamp(now-relativedelta(months=1)),
        "6months":datetime.timestamp(now-relativedelta(months=6)),
        "year":datetime.timestamp(now-relativedelta(years=1))
    }

    cut_off = DT[time]
    output = []
    for item in data:
        if item["ts"] > cut_off:
            output.append(item)
    return output

def results_today(data):
    """
        Gets only items scanned today

        Parameters
            data:   list of dicts containing "ts" timestamp and "value" category
        
        Returns
            output: list of dicts " (only items scanned today)
    """
    output = []
    today = datetime.now().date()
    for item in data:
        if datetime.fromtimestamp(item["ts"]).date() == today:
            output.append(item)
    return output

def count_types(data):
    """
        Count the total number of items in each category

        Parameters
            data: list of dicts containing "ts" timestamp and "value" category
        
        Returns
            count:  list containing each type, corresponding to TYPE
    """
    count = [0]*len(TYPES)
    for item in data:
        count[TYPES.index(item["value"])] += 1
    return count

def count_days(data):
    """
        Count the total number of items scanned on each day

        Parameters
            data: list of dicts containing "ts" timestamp and "value" category
        
        Returns
            x:  list containing string of every day from first data item to today
            y:  list containing total count in each day
    """
    if len(data) == 0:
        return [],[]
    
    today = datetime.now().date()
    s = datetime.fromtimestamp(data[0]["ts"]).date()
    x = []
    while s - today <= timedelta(0):
        x.append(s.strftime("%d/%m/%Y"))
        s = (s + timedelta(days=1))

    y = [0]*len(x)
    for item in data:
        date = datetime.fromtimestamp(item["ts"]).strftime("%d/%m/%Y")
        i = x.index(date)
        y[i] += 1
    return x,y

def count_times(data):
    """
        Count the total number of items scanned at each hour

        Parameters
            data: list of dicts containing "ts" timestamp and "value" category
        
        Returns
            x:  list containing 0 to 23 (hours)
            y:  list containing total count in each hour slot
    """
    if len(data) == 0:
        return [],[]
    
    x = [i for i in range(24)]
    y = [0]*len(x)
    for item in data:
        h = datetime.fromtimestamp(item["ts"]).hour
        y[h] += 1
    return x,y

def get_dt(ts):
    """
        Gets a human-readable datetime string from a timestamp

        Parameters:
            ts: timestamp
        
        Returns
            string: dd/mm/yyyy h:m
    """
    dt = datetime.fromtimestamp(ts)
    return dt.strftime("%d/%m/%Y %H:%M")

def dashboard_data(time):
    """
    Get the data to display on the dashboard screen

    Returns
        data:   dict
            "xs":           list of lists for Pyplot graphs
            "ys":           list of lists for Pyplot graphs
            "table_data":   list of lists of columns for Pyplot table
    """
    data = get_user_telemetry()
    items = results_in_time(data, time)

    x1,y1 = count_days(items)
    x2,y2 = count_times(items)
    td = [[get_dt(i["ts"]) for i in reversed(items)],
          [i["value"] for i in reversed(items)]]

    data_output = {
        "xs":[
            TYPES,
            x1,
            x2
        ],
        "ys":[
            count_types(items),
            y1,
            y2
        ],
        "table_data":td
    }

    return data_output

def live_data():
    """
    Get the data to display on the live screen

    Returns
        data:   dict
            "recent": most recent item type
            "today_count": number of items today
            "xs":   list of lists for Pyplot graphs
            "ys":   list of lists for Pyplot graphs  
    """
    data = get_user_telemetry()
    items = results_today(data)
    n = len(items)

    if n>0:
        recent = items[n-1]["value"]
    else:
        recent = None
    
    x0,y0 = count_times(items)

    data_output = {
        "recent":recent,
        "today_count":n,
        "xs":[
            x0
        ],
        "ys":[
            y0
        ]
    }
    return data_output

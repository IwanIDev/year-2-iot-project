"""
Gets and interprets thingsboard data to be displayed
"""
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import random

TYPES = ["PLASTIC","PAPER","GLASS","GENERAL WASTE","FOOD"]

def rand_last_week():
    # TEMPORARY FOR GENERATING DUMMY DATA
    # RETURNS RANDOM TIMESTAMP IN THE LAST WEEK
    rand_time_today = datetime.now().replace(hour=random.randint(0,23),minute=random.randint(0,59))
    rand_time_today = rand_time_today - timedelta(days=random.randint(0,25))
    return datetime.timestamp(rand_time_today)

dummy_json = {
    "category":[
        {"ts": rand_last_week(),
         "value":random.choice(TYPES)} for _ in range(200)
    ]
}

def sort(data):
    output = []
    for item in data:
        if len(output) == 0:
            output.append(item)
        else:
            for i in range(len(output)):
                if item["ts"] > output[i]["ts"]:
                    if i == len(output)-1:
                        output.append(item)
                    continue
                output.insert(i,item)
                break
    return output

DATA = sort(dummy_json["category"])

def results_in_time(data,time):
    """
    Gets all categories in a given timeframe

    Parameters:
        data:   list of dicts containing timestamp 'ts' and category 'value'
        time:   string containing one of:
            7days, 14days, month, 6months, year, all
    
    Returns:
        list:   categories within the given timeframe
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
    output = []
    today = datetime.now().date()
    for item in data:
        if datetime.fromtimestamp(item["ts"]).date() == today:
            output.append(item)
    return output

def count_types(data):
    count = [0]*len(TYPES)
    for item in data:
        count[TYPES.index(item["value"])] += 1
    return count

def count_days(data):
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
    if len(data) == 0:
        return [],[]
    
    x = [i for i in range(24)]
    y = [0]*len(x)
    for item in data:
        h = datetime.fromtimestamp(item["ts"]).hour
        y[h] += 1
    return x,y

def dashboard_data(time):
    items = results_in_time(DATA,time)

    x1,y1 = count_days(items)
    x2,y2 = count_times(items)

    data = {
        "xs":[
            TYPES,
            x1,
            x2
        ],
        "ys":[
            count_types(items),
            y1,
            y2
        ]
    }

    return data

def live_data():
    items = results_today(DATA)
    n = len(items)
    
    x0,y0 = count_times(items)

    data = {
        "recent":items[n-1]["value"],
        "today_count":n,
        "xs":[
            x0
        ],
        "ys":[
            y0
        ]
    }
    return data
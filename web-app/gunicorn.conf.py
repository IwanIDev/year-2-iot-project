from multiprocessing import cpu_count


def max_workers():    
    return cpu_count()

ADDRESS = "0.0.0.0"
PORT="8080"

accesslog = "-"

bind = ADDRESS + ':' + PORT
max_requests = 1000
workers = max_workers()

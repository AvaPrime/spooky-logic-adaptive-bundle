from prometheus_client import start_http_server, Counter, Histogram
from time import time, sleep
from contextlib import contextmanager

TASKS = Counter("spooky_worker_tasks_total", "Worker tasks completed", ["playbook","status"])
LAT = Histogram("spooky_worker_task_latency_seconds", "Worker task latency (s)", buckets=[0.1,0.25,0.5,1,2,5,10])

def boot_metrics_server(port: int = 8000):
    """Starts an HTTP server for exposing Prometheus metrics.

    Args:
        port: The port to start the server on.
    """
    start_http_server(port)

@contextmanager
def timed_task(playbook: str):
    """A context manager for timing tasks and collecting metrics.

    This context manager times the execution of a task and records metrics
    on the number of tasks completed and their latency. It also handles
    exceptions and records errors.

    Args:
        playbook: The name of the playbook being timed.
    """
    t0 = time()
    try:
        yield
        TASKS.labels(playbook=playbook, status="ok").inc()
    except Exception:
        TASKS.labels(playbook=playbook, status="err").inc()
        raise
    finally:
        LAT.observe(time()-t0)

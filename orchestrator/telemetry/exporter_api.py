from time import time
from typing import Callable
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse
from fastapi import FastAPI

REQS = Counter("spooky_api_requests_total", "API requests", ["path", "method", "code"])
LAT = Histogram("spooky_api_latency_seconds", "API latency (s)", buckets=[0.05,0.1,0.25,0.5,1,2,5])

class MetricsMiddleware(BaseHTTPMiddleware):
    """A middleware for collecting metrics on API requests.

    This middleware collects metrics on the number of requests, latency, and
    response codes for each API endpoint.
    """
    async def dispatch(self, request: Request, call_next: Callable):
        """Dispatches a request and collects metrics.

        Args:
            request: The request to dispatch.
            call_next: The next middleware or endpoint to call.

        Returns:
            The response from the next middleware or endpoint.
        """
        start = time()
        try:
            resp = await call_next(request)
            code = getattr(resp, "status_code", 500)
        except Exception:
            code = 500
            raise
        finally:
            dur = time() - start
            REQS.labels(path=request.url.path, method=request.method, code=str(code)).inc()
            LAT.observe(dur)
        return resp

def mount_metrics(app: FastAPI, path: str = "/metrics"):
    """Mounts the metrics endpoint on a FastAPI application.

    This function adds a /metrics endpoint to the given FastAPI application
    that exposes the latest Prometheus metrics. It also adds the
    `MetricsMiddleware` to the application to collect metrics on API requests.

    Args:
        app: The FastAPI application to mount the metrics endpoint on.
        path: The path to mount the metrics endpoint on.
    """
    @app.get(path)
    def _metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
    app.add_middleware(MetricsMiddleware)

from starlette.middleware.base import BaseHTTPMiddleware
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
import time

tracer = trace.get_tracer(__name__)

class OpenTelemetryMiddleware(BaseHTTPMiddleware):
    """A middleware for adding OpenTelemetry tracing to requests."""
    async def dispatch(self, request, call_next):
        """
        Dispatches a request and adds OpenTelemetry tracing.

        Args:
            request: The request to dispatch.
            call_next: The next middleware or endpoint to call.

        Returns:
            The response from the next middleware or endpoint.
        """
        with tracer.start_as_current_span(f"HTTP {request.method} {request.url.path}") as span:
            start = time.time()
            try:
                response = await call_next(request)
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise
            finally:
                duration = time.time() - start
                span.set_attribute("http.method", request.method)
                span.set_attribute("http.path", request.url.path)
                span.set_attribute("http.duration", duration)
            return response

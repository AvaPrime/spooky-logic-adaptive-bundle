FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY api /app/api
COPY orchestrator /app/orchestrator
COPY playbooks /app/playbooks
COPY policies /app/policies
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "info"]

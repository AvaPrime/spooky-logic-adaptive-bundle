FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY orchestrator /app/orchestrator
COPY playbooks /app/playbooks
COPY policies /app/policies
CMD ["python", "-m", "orchestrator.worker"]

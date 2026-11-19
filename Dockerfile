FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py translations.py .
COPY templates ./templates
COPY static ./static
USER 10001:10001
EXPOSE 8443
CMD ["gunicorn", "--bind", "0.0.0.0:8443", "--workers", "1", "--threads", "4", "--timeout", "120", "--certfile", "/config/tls.crt", "--keyfile", "/config/tls.key", "--access-logfile", "-", "app:app"]

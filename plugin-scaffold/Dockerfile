FROM python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f

WORKDIR /app

COPY requirements.lock .
RUN pip install --no-cache-dir --require-hashes -r requirements.lock

COPY . .

ENV PORT=8000 WISDOMTWIN_ENV=production HOST=0.0.0.0 PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["python", "server.py"]

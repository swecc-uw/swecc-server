FROM python:3.9 AS development

WORKDIR /app
COPY requirements-server.txt .
RUN apt-get update && apt-get install -y \
    gunicorn \
    && rm -rf /var/lib/apt/lists/*
RUN pip install -r requirements-server.txt
COPY . .

FROM development AS production

WORKDIR /app/server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "server.wsgi", "--workers", "5"]

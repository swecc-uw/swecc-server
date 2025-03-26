FROM python:3.9 AS development

WORKDIR /app
COPY server.requirements.txt .
RUN apt-get update && apt-get install -y \
    gunicorn \
    && rm -rf /var/lib/apt/lists/*
RUN pip install -r server.requirements.txt
COPY . .

FROM development AS production

WORKDIR /app/server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "server.wsgi"]
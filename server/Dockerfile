# FROM python:3.9

# WORKDIR /app

# ENV PYTHONUNBUFFERED=1

# COPY requirements.txt .
# RUN pip install -r requirements.txt

# COPY . .

# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "server.wsgi:application"]

# syntax=docker/dockerfile:1
FROM python:3
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY . /app/
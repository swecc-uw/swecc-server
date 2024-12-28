FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install gunicorn -y
RUN pip install -r requirements.txt

COPY . .

WORKDIR /app/server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "server.wsgi"]

# CMD ["python3", "server/manage.py", "runserver", "0.0.0.0:8000"]
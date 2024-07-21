FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install gunicorn -y
RUN pip install -r requirements.txt

COPY . .

# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "server.wsgi:application"]
CMD ["python", "server/manage.py", "runserver", "0.0.0.0:8000"]

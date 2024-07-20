FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN apt-get update && apt-get install gunicorn -y

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "server.wsgi:application"]

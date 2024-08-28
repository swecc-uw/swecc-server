FROM python:3.9
# RUN apt-get update && apt-get install gunicorn -y

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "server/server.wsgi:application"]
RUN python3 server/manage.py migrate
CMD ["python3", "server/manage.py", "runserver", "0.0.0.0:8000"]
# CMD ["sleep","3600"]
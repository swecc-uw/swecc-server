# swecc-server

## Getting Started

### Virtual Environment

We recommend using two separate virtual environments for development and production. Below is how you set up your dev venv, but you can replace credentials with your production credentials to create a production venv.

```bash
python3 -m venv dev.venv
source dev.venv/bin/activate
pip install -r requirements.txt
```

Add env variables to `dev.venv/bin/activate`

```bash
export DJANGO_DEBUG=True
export DB_HOST=db
export DB_NAME=postgres
export DB_PORT=5432
export DB_USER=root
export DB_PASSWORD=password
```

## Reference

| task | command | 
| --- | --- |
| run server locally (requires prod.venv) | `python server/manage.py runserver` |
| run server in docker (requires dev.venv) | `docker compose up --build` |

## Runbook


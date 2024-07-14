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

### Cron job for clearing 1 day old auth keys

`0 * * * * ~/swecc-server/venv/bin/python /swecc-server/server/manage.py prune_authkeys`

## Reference

| task | command | 
| --- | --- |
| run server locally (requires prod.venv active) | `python server/manage.py runserver` |
| run server in docker (requires dev.venv active) | `docker-compose up` |
| generate openapi schema | `python server/manage.py spectacular --color --file schema.yml` |
| swagger ui | `docker run -p 80:8080 -e SWAGGER_JSON=/schema.yml -v /Users/emm12/repos/swecc-server/schema.yml:/schema.yml swaggerapi/swagger-ui` |

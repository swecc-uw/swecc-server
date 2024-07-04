# swecc-server

## Getting Started

### Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Add env variables to `venv/bin/activate`

```bash
export DB_HOST= <...>
export DB_NAME= <...>
export DB_PORT= <...>
export DB_USER= <...>
export DB_PASSWORD= <...>
```

## Reference

| task | command | 
| --- | --- |
| run server | `python server/manage.py runserver` |
| generate openapi schema | `python server/manage.py spectacular --color --file schema.yml` |
| swagger ui | `docker run -p 80:8080 -e SWAGGER_JSON=/schema.yml -v /Users/emm12/repos/swecc-server/schema.yml:/schema.yml swaggerapi/swagger-ui` |
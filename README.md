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

```bash
curl -X PUT -H "Authorization: Api-Key $VERIFICATION_KEY" -H "Content-Type: application/json" -d '{"username": "elimelt", "discord_username": "elimelt", "discord_id": 1234}' http://localhost:8000/members/verify-discord/
```

## Runbook

### Creating and verifying an account locally

1. Start the application
```bash
docker compose -f docker-compose.local.yml up --build
```

2. Run the migrations
```bash
docker exec -it swecc-server-web-1 python server/manage.py migrate
```

3. Create a regular user on the frontend

4. Create a superuser
```bash
docker exec -it swecc-server-web-1 python server/manage.py createsuperuser
```

5. Access the admin panel at `http://localhost:8000/admin/`, and login with the superuser credentials you created.

6. In the admin panel, create a new API key. Doesn't matter what you name it, but make sure to **copy the key somewhere safe**. I recommend putting it in your `dev.venv/bin/activate` file, e.g. `export VERIFICATION_KEY=your_key_here`.

7. Verify your discord account, using the API key you just created, and the **non-superuser** credentials you created in step 3.
```bash
curl -X PUT \
-H "Authorization: Api-Key <VERIFICATION_KEY>" \
-H "Content-Type: application/json" \
-d '{"username": <YOUR_USER>, "discord_username": <YOUR_DISCORD>, "discord_id": <SOME_INT>}' \
http://localhost:8000/members/verify-discord/
```

### Creating user with script
1. Windows

**Warning**: Before running the script make sure to setup dev env first and migrate the db.

- Run `script/userCreate.bat <username>` to create a new verified user. Default password for each created user 
when using the script is `123456`.
- Run `script/makeAdmin.bat <username>` to make an existing user admin
- Run `script/populateUser.bat <num users>` to add `<num user>` verfied users dev db.

2. Unix
- To be developed

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

### Network

Create a docker network to use while testing locally with docker-compose

```bash
docker network create swecc-default
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
5. Grant admin acess
```bash
docker exec -it swecc-server-web-1 python server/manage.py create_admin --username yourUserName
```
6. Access the admin panel at `http://localhost:8000/admin/`, and login with the superuser credentials you created.

7. In the admin panel, create a new API key. Doesn't matter what you name it, but make sure to **copy the key somewhere safe**. I recommend putting it in your `dev.venv/bin/activate` file, e.g. `export VERIFICATION_KEY=your_key_here`.

8. Verify your discord account, using the API key you just created, and the **non-superuser** credentials you created in step 3.
```bash
curl -X PUT \
-H "Authorization: Api-Key <VERIFICATION_KEY>" \
-H "Content-Type: application/json" \
-d '{"username": <YOUR_USER>, "discord_username": <YOUR_DISCORD>, "discord_id": <SOME_INT>}' \
http://localhost:8000/members/verify-discord/
```
```bash
For local development verify
docker exec -it swecc-server-web-1 python manage.py verify_account --username yourUsername
```

### Creating user with script
1. Docker
```bash
docker exec -it swecc-server-web-1 python server/manage.py createsuperuser

### Out of space

Everything is run in EC2. A common problem seems to be running out of space, probably because of our log files. If you're ever in what seems to be an unrecoverable state (e.g. can't remove or clean because writes fail due to no more space), try this:

After sshing in, kill all docker

```bash
sudo systemctl stop docker
sudo rm -rf /var/lib/docker
```
Then, reboot

```bash
sudo reboot
```

Cleanup

```bash
sudo apt autoclean
```

Restart docker 

```bash
sudo systemctl start docker
sudo docker network create swag-network
pushd ~/swag; docker-compose up -d; popd
```

Finally, restart containers by triggering a deploy. 


### Deploy not working

Just ssh and remove the current `actions-runner` directory and follow [these docs](https://docs.github.com/en/actions/hosting-your-own-runners/managing-self-hosted-runners/configuring-the-self-hosted-runner-application-as-a-service) to add a new actions runner, which should pick up the job shortly after. You should start the runner as a service

```bash
sudo ./svc.sh install
sudo ./svc.sh start
```

### HTTPS not working

If you see this in the logs

```
You're accessing the development server over HTTPS, but it only supports HTTP.
```

and in network tab you get status `(failed)net::ERR_CONNECTION_REFUSED`, you might need to start the swag container.

```
cd ~/swag; docker-compose up -d
```

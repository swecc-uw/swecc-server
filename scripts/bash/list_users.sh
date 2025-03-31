#!/bin/bash

command="python server/manage.py list_users"

# execute
docker exec -it swecc-server-web-1 bash -c "$command"

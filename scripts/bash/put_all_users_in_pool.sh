#!/bin/bash

command="python server/manage.py put_all_users_in_pool"

# execute
docker exec -it swecc-server-web-1 bash -c "$command"

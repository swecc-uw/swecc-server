#!/bin/bash

command="python server/manage.py pair"

# execute
docker exec -it swecc-server-web-1 bash -c "$command"


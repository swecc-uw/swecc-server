#!/bin/bash

check num users provided or fall back
if [ -z "$1" ]; then
    echo "Number of users to create is required. Defaulting to 1."
    numUsers=1
else
    numUsers="$1"
fi

echo "Creating $numUsers users..."

# create users
for (( i=1; i<=$numUsers; i++ ))
do
    # dir of current script
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
    # exec user_create.sh
    "$SCRIPT_DIR/create_user.sh"
done

echo "Users created successfully."
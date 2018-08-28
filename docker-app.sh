#!/bin/sh
# down and rebuild the app container
echo "RESTARTING THE DOCKER app CONTAINER"
docker-compose stop web
docker-compose kill web
# -f, --force   don't ask to confirm removal
docker-compose rm -f web
docker-compose up -d --build web
#read -p "Press any key to continue... " -n 1 -s
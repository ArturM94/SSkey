# SSkey
REST application 

[![Build Status](https://travis-ci.org/LialinMaxim/SSkey.svg?branch=Development)](https://travis-ci.org/LialinMaxim/SSkey)

## Getting started

1. Install [Docker](https://docs.docker.com/engine/installation/) and run the docker-machine:

    ```shell
    docker-machine start
    ```

2. Deploy the project:

    ```shell
    docker-deploy.sh
    ```

3. Check a list containers:

    ```shell
    docker ps
    ```

4. Wait a minute until the server starts and check app service logs:

    ```shell
    docker-compose logs app
    ```

5. If the application was started visit a default docker-machine IP address:

    [http://192.168.99.100:5000](http://192.168.99.100:5000)

If you need to check your docker-machine IP address use:

```shell
docker-machine ip
```

If you need to make some changes to the project without affecting the server and rebuild it use:

```shell
docker-app.sh
```

## Local launch

1. Create `.env` file in `src/app` folder and write the environment variables into it.

2. Environment variables for application:

    ```shell
    SECRET_KEY=yor_secret_key
    ``` 
    
    Environment variables for your PostgreSQL database:
    
    ```shell
    POSTGRES_USER=your_postgres_user
    POSTGRES_PASS=your_postgres_password
    POSTGRES_NAME=your_postgres_db_name
    POSTGRES_HOST=localhost
    ``` 

3. Install dependencies:

    ```shell
    pip install -r src/app/requirements.txt
    ```

4. Run the application:

    ```shell
    python src/manage.py runserver
    ```

5. Visit [http://localhost:5000](http://localhost:5000)

## Flask Application Structure 

```

.
├── docker-compose.yml
├── README.md
└── src
    ├── app
    │   ├── base.py
    │   ├── config.py
    │   ├── errors
    │   │   ├── handlers.py
    │   │   └── __init__.py
    │   ├── __init__.py
    │   ├── migrate.py
    │   ├── models.py
    │   ├── requirements.txt
    │   ├── resources.py
    │   ├── routes.py
    │   ├── shemas.py
    │   └── swagger.yaml
    ├── boot.sh
    ├── Dockerfile
    ├── __init__.py
    ├── manage.py
    └── tests
        ├── __init__.py
        └── test_basic.py

```

## Development

Create a new branch off the **develop** branch for features or fixes.

After making changes rebuild images and run the app:

```shell
docker-compose build
docker-compose run -p 5000:5000 web python manage.py
```

## Tests

Standalone unit tests run with:

```shell
python -m pytest src/tests
```

## Postgresql

Install [postgresql](https://www.postgresql.org/download/) and run:
```shell
python base.py # database config
python migrate.py # in order to create database
python src/manage.py initdb # create database from models
python src/manage.py dropdb # delete database
python src/manage.py recreatedb # delete and create database
```

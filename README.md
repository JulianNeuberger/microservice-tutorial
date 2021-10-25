# Microservice Tutorial
## Setup
1. Setup the database

    1.1. Install PostgreSQL at version 13.4 from https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
    
    1.2. Open a PostgreSQL shell (run `psql.exe` on Windows)
    
    1.3. Open a connection to the default database via the credentials you set during the previous step
    
    1.4. Create a new database via `CREATE DATABASE tutorial;`
    
    1.5. Create a new user via `CREATE USER tutorial WITH PASSWORD 'tutorial';` 
    
    1.6. Open a new connection to the newly created database with the root user
    
    1.7. Grant the user from step 1.5 all rights on the database from step 1.4. via `GRANT ALL PRIVILIGES ON DATABASE tutorial TO USER tutorial;`

2. Setup the tutorial server

    2.1. Install python at version 3.8

    2.2. Clone the tutorial code from https://github.com/JulianNeuberger/microservice-tutorial 

    2.3. Enter the cloned directory

    2.4. Install the required python packages via `pip install –r requirements.txt`

    2.5. Rename the `config.template.ini` to `config.ini`

    2.6. Fill in the needed database information, i.e. `POSTGRES_DBNAME`, 
    `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`

    2.7. Fill in the login info to the RabbitMQ instance provided by us

3. Start the server by running `python -m tutorial.server`

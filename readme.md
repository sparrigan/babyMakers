# Clone repo

Clone the repo to your local machine.


# Install dependencies

## Install postgres RDBMS

Use homebrew to install postgres: `brew install postgres`.

(If you don't have homebrew - a great package installer for mac, then see [http://brew.sh/][http://brew.sh/])

If you've never setup a postgres database then use: `initdb /usr/local/var/postgres -E utf8` to setup a database


## Setup virtual environment

If you don't have virtual environment, install using `pip install virtualenv`

Then setup a virtual environment for the project, this will install all the python packages needed.

```
cd babyMakers
virtualenv venv
```

Now activate the virtual environment: `source venv/bin/activate`

Now you have the virtual environment set up, install all packages neeeded by babyMakers `pip install -r requirements.txt`


# Create and setup database

You should now have the postgres RDBMS installed. Start the postgres server by typing `postgres -D /usr/local/var/postgres`

Now open up another terminal window and type `createdb babyMakers`. This will also create a user for the database, with the same name as the system user who issued the `creatdb` command. Note that if you call the database a different name other than 'babyMakers' then you will need to alter the associated `DATABASE` environment variable in babyMaker.config.

Now assign a password to this user, run the psql command line interface in a terminal window whilst the postgres server is still running: `psql babyMakers`. Then at the psql prompt `ALTER USER yourusername WITH PASSWORD 'yournewpassword';` (where `yourusername` is the system username you ran createdb with - you can check what this is by running `\du` from a psql prompt - and `yournewpassword` is the password you want for this user). Keep a note of your password for the next step.

# Acquire themoviedb api keys

babyMakers makes use of the fantastic themoviedb api to fetch movie information. To acquire a key for themoviedb api, signup at https://www.themoviedb.org/account/signup.

After you receive email authentication, login and click on 'API'
under "Request an API Key" click on 'here'
Click on 'developer' and fill out form with appropriate details
Check email for API Key
Add API Key to config variable file
Consider donation.

# Set credentials

## Create a configuration file in root directory of project

This file will contain all your dirty little secrets (including passwords).

Create a file called babyMakers.cfg in root project directory: `touch babyMakers.cfg`.

In this file, write the following variable definitions:

```
export PG_USERNAME='your_postgres_username'
export PG_PASSWORD='your_postgres_password'
export DATABASE='localhost/babyMakers'
export DEBUG=True
export API_KEY = 'your_api_key'
```

Where you will need to replace the 'your...' string values with your respective data.

## Register config file as environment variables

To run locally, you will then need to source the environment variables that you have in your babyMakers.cfg file. You can do this from a terminal prompt by typing: `source babyMakers.cfg` from within the root project directory.



<!-- source babyMakers.cfg

http://stackoverflow.com/questions/14904142/export-variables-defined-in-another-file -->

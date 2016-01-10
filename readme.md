# babyMakers

babyMakers is a tool for investigating whether movie-stars have had an influence on baby-naming throughout history, by providing an interface for plotting significant movie releases by an actor/actress against babyname trends. babyMakers also calculates a significance value for whether releases by a given movie-star leads increases in occurences of the associated baby name.

The tool is available online at  xxxx. To recreate the project yourself locally, take the following steps.

## Clone repo

Clone the repository to your local machine

## Install dependencies

### Install postgres RDBMS

Use homebrew to install postgres: `brew install postgres`.

(If you don't have homebrew - a great package installer for mac, then see [http://brew.sh/][http://brew.sh/])

If you've never setup a postgres database then use: `initdb /usr/local/var/postgres -E utf8` to setup a database


### Setup virtual environment

If you don't have virtual environment, install using `pip install virtualenv`

Then setup a virtual environment for the project, this will install all the python packages needed.

```
cd babyMakers
virtualenv venv
```

Now activate the virtual environment: `source venv/bin/activate`

Now you have the virtual environment set up, install all packages neeeded by babyMakers `pip install -r requirements.txt`


## Create and setup database

You should now have the postgres RDBMS installed. Start the postgres server by typing `postgres -D /usr/local/var/postgres`

Now open up another terminal window and type `createdb babyMakers`. This will also create a user for the database, with the same name as the system user who issued the `creatdb` command. Note that if you call the database a different name other than 'babyMakers' then you will need to alter the associated `DATABASE` environment variable in babyMaker.config.

Now assign a password to this user, run the psql command line interface in a terminal window whilst the postgres server is still running: `psql babyMakers`. Then at the psql prompt `ALTER USER yourusername WITH PASSWORD 'yournewpassword';` (where `yourusername` is the system username you ran createdb with - you can check what this is by running `\du` from a psql prompt - and `yournewpassword` is the password you want for this user). Keep a note of your password for the next step.

## Acquire themoviedb api keys

babyMakers makes use of the fantastic themoviedb api to fetch movie information. To acquire a key for themoviedb api, signup at https://www.themoviedb.org/account/signup.

After you receive email authentication, login and click on 'API'
under "Request an API Key" click on 'here'
Click on 'developer' and fill out form with appropriate details
Check email for API Key
Add API Key to config variable file
Consider donation.

## Set credentials

### Create a configuration file in root directory of project

This file will contain all your dirty little secrets (including passwords).

Create a file called babyMakers.cfg in root project directory: `touch babyMakers.cfg`.

In this file, write the following variable definitions:

```
PG_USERNAME='your_postgres_username'
PG_PASSWORD='your_postgres_password'
DATABASE='localhost/babyMakers'
DEBUG=True
API_KEY = 'your_api_key'
```

Where you will need to replace the 'your...' string values with your respective data.

### Register config file as environment variables

To run locally, you will then need to source the environment variables that you have in your babyMakers.cfg file. You can do this from a terminal prompt by typing:

```
set -a
source babyMakers.cfg
set +a
```

...from within the root directory of your project folder.

## Populating the database

You need to acquire a set of csv files of babynames in order to populate the database (https://ssa.gov/oact/babynames/limits.html). babyMakers looks for a folder containing all the necessary csv files in a 'names' directory within the root project directory by default, but you can change the path to the file in the CSV_PATH field of babyMakers.cfg.

Making sure you are running your virtual environment, with environment variables registered from the config file, now run `python model.py` from the root project directory in order to poulate the postgresql database with values from the csv files. Typically this takes 5-10 minutes, and a prompt should provide information on progress.

## Run the application server

Making sure that you still have the postgresql server running (if not, you can run it by typing `postgres -D /usr/local/var/postgres` into a free terminal window), now run the application server by typing `python controller.py` from the project root directory. This will serve the application to a port on localhost (check terminal readout for the exact port, typically 5000). You can then view the application by opening a web browser and navigating to 'localhost:5000' (or 'localhost:<xxxx>' if the port is some value <xxxx> other than 5000). 

<!-- source babyMakers.cfg

http://stackoverflow.com/questions/14904142/export-variables-defined-in-another-file -->

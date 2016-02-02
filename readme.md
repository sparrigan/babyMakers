# Celebrodisiac

Celebrodisiac is a tool for investigating whether movie-stars have had an influence on baby-naming throughout history, by providing an interface for plotting significant movie releases by an actor/actress against babyname trends. Celebrodisiac also calculates a significance value for whether releases by a given movie-star leads increases in occurences of the associated baby name.

# Local build instructions

The tool is available online at [http://www.celebrodisiac.com/][8]. To recreate the project yourself locally, take the following steps.

## Clone repo

Clone the repository to your local machine

## Install dependencies

### Install postgres RDBMS

On mac, use homebrew to install postgres: `brew install postgres`.

(If you don't have homebrew - a great package installer for mac, then see [http://brew.sh/][http://brew.sh/])

On linux, use `apt-get install postgresql postgresql-contrib`

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



# Deployment Instructions

Deploying the app may involve some complications, here instructions for deploying using NGINX and uWSGI on an AWS ec2 instance.

## Setting up an ssh connection to the server

## Clone repo into project directory

Create project directory
```
mkdir babyMakers
cd babyMakers
```
Clone repo
```
git clone <repo_url>
```


## Check security settings

It is worth checking that AWS has the correct security settings for incoming and outgoing traffic - otherwise this could be a frustrating problem to debug later on. You can check these settings in your aws web control panel, under the ec2 dashboard. Navigate to your list of instances (INSTANCES -> Instances on left tree navigation panel). Scroll to the right until you see the last column of information about your instance - titled 'Securty Groups'. This shows the setting groups that your instance currently belongs to, click on the group you wish to check, and you will be taken to the Security Group page. At the bottom of this page are several tabs, including 'Inbound' and 'Outbound'. Click the 'Edit' button on the 'Input' tab, and in the pop-up window that appears, choose HTTP from the 'Type' dropdown. Ensure that Source is set to 'Anywhere' (0.0.0.0/0). Perform a similar check with the 'Outbound' tab. Should you have problems with SSH settings then it's also worth checking the secutity settings for this in the respective 'Type' dropdowns

## Create a virtual environment

Install virtual environment

```
sudo pip install virtualenv
virtualenv venv
```
Activate virtual environment

```
source venv/bin/activate
```

## Installing requirements.txt

The requirements.txt included in the repo lists all of the python dependencies. Install all modules on this list by running the following command within the project directy and *from within your project virtual environment* (however, before attempting this, see the notes below, which may require some prior installation through `apt-get`):

```
pip install -r requirements.txt
```

Note that on ubuntu scipy has some dependencies that may need to be installed with `apt-get`. Also, if using an ec2 AWS instance (or other low memory server), you may need to manually allocate more swap memory. The below code allocates extra swap, installs dependencies, then installs scipy and then unallocates swap memory. Within different deployment environments, all, some or none of this may be necessary.

```
# Allocate swap memory
sudo /bin/dd if=/dev/zero of=/var/swap.1 bs=1M count=1024
sudo /sbin/mkswap /var/swap.1
sudo /sbin/swapon /var/swap.1

# Install dependencies and scipy
sudo apt-get install -y libatlas-base-dev gfortran python-dev build-essential g++
sudo pip install numpy
sudo pip install scipy

# Unallocate swap
sudo swapoff /var/swap.1
sudo rm /var/swap.1
```

Also note that module pscycopg2 from requirements.txt (required for communicating with postgres DB) has the following dependency, that needs to be installed using `apt-get` prior to running `pip install -r requirements.txt`:

```
sudo apt-get install libpq-dev
```


## Setting up postgresql server

1. Install postgresql on server
```
apt-get update
sudo apt-get install postgresql postgresql-contrib
```
This *should* also begin running the postgress server. You can check this by running `ps aux`, or by logging into the postgres interactive terminal -psql (see below for how to do this - it most likely requires changing user).

2. Setup user
postgres is the default user for the DB, which is setup as a linux user. You will need to login to postgres with that user - at which point you will be prompted to change your password.
Enter the following
```
sudo -u postgres psql postgres
```
If not prompted to do so, you can change the password for postgres user at the resulting psql prompt with this command:
```
\password postgres
```

You now need to create a database which the babyMakers model can populate. You can do this either from a psql prompt: `CREATE DATABASE babyMakers;` or from bash prompt (when not logged into the database): `sudo -u postgres createdb babyMakers`.

You can inspect your database within the postgres interactive terminal at any time by running `psql babyMakers` from a user that has access rights (eg: do `sudo su postgres` first to change to postgres user). Within the interactive terminal there are [various commands][4] that can be used to inspect the DB contents, and SQL commands can be issued (in capitals, with line-termination by semicolon).


## Install uWSGI, create wsgi.py amd configure uWSGI

1. Install uwsgi with pip - ensuring you are in the project directory and running your project virtual environment:
```
pip install uwsgi
```

2. Create a `wsgi.py` file in the root of the project-directory and enter the following

```
from controller import application

if __name__ == "__main__":
	application.run()
```

Note that this relies on the fact that the flask instance in `controller.py` is called 'application' (i.e. `application = Flask(__name__)`). Should it be given any other name, then `wsgi.py` needs to be amended accordingly.

3. Create a `<project-name>.ini` file in the root of the project-directory. Then add the following configurations to the file for uWSGI:

```
[uwsgi]
module = wsgi

master = true
processes = 1

socket = <project-name>.sock
chmod-socket = 660
vacuum = true

die-on-term = true
```

Note that processes is set to 1 in this case because of API limiting, but generally would be set to about 5.

## Create and start upstart script

1. Upstart scripts reside in `/etc/init` and are launched when the system starts - enabling the server to resume on a restart. Create a file `/etc/init/<project-name>.conf` and add the following:

```
description "uWSGI server instance configured to serve project"

console log

start on runlevel [2345]
stop on runlevel [!2345]

setuid <user>
setgid www-data

script
	PATH=$PATH:/path/to/project-directory/venv/bin
	set -a
		. /path/to/project-directory/babyMakers.cfg
	set +a

	cd /home/ubuntu/babyMakers/
	uwsgi --ini /path/to/project-directory/babyMakers.ini #--logto /path-to-log-file/uwsgi_log.out
end script
```

There are a few subtle points to note about the syntax in upstart files.

* <user> should be replaced by the username to run the server (typically ubuntu by default on AWS).
* `PATH` should point to the bin directory of then projects virtual environment.
* `.` is used instead of `source`.
* `set -a` reads definitions that follow (in this case in a file) as environment variables. `set +a` ends this.
* It is possible to either declare individual shell commands using `exec` or all-together within `script .. end script` blocks as above. However, *it is crucial to take care mixing the two* as they will not necessarily run in order (eg: if the uWSGI command above was in a seperate `exec` command it might try and run before the script block had assigned the environment variables it later relies on).
* console log allows logging to `/var/log/upstart/<conf-filename>.log` (see below), including `echo` statements with script blocks.

2. Begin the upstart script (and consequently uWSGI server in the background) with `sudo start <project-name>`, where `<project-name>` is the name we gave to the `.conf` file in `/etc/init` (but not including the `.conf` extension). We can also stop the process with `sudo stop <project-name>`. Take care to note the alert given after starting the upstart task - if it reads 'stop/waiting' then the task has not begun.

## Install, configure and start NGINX

1. Install NGINX with `apt-get`

```
apt-get install nginx
```
(instructions on checking that NGINX is updated to the latest version can be found [here][7])

2. Configure NGINX by adding a new configuration file at `/etc/nginx/conf.d/<project-name>.conf`. Add the following to this file:

```
server {
  listen 80;
  server_name <your-ip-address>;

  location / {
    include uwsgi_params;
    uwsgi_pass unix:/path/to/project-directory/<project-name>.sock;
  }
}
```

Note that most importantly, the name of the file `<project-name>.sock` must agree with the name givin in the uWSGI `.ini` file (see above).

**Importantly:** Also *comment out the following line* within `/etc/nginx/nginx.conf`:

```
include /etc/nginx/sites-enabled/*;
```  

3. (Re)start NGINX with the command `sudo service nginx restart`.


## Set host parameter in controller.py

When running locally, the flask command `application.run()` within `controller.py` does not take an argument (which runs it only locally). However, to ensure that it serves to all IP addreses we must replace this with the following:

```
application.run(host = '0.0.0.0')
```

Make sure that this line is uncommented at the bottom of `controller.py` (and that `application.run()` *is* commented or removed).


## Writing upstart script

The upstart script will run whenever the system starts and begin the serving process.
Upstart scripts are kept in `/etc/bin`, and [this][1] is a great resource for syntax in startup scripts. Also note that `.` should be used to source files (see [this][2] stackoverflow comment).

Note that you can use `echo $VAR` to check the value of an environment variable `VAR`. See [here][3] for more info on environment variables in general.

## Sending babyname csv files to server

In order to populate the postgres DB, the babyname data must be present in a set of CSV files (obtainable from the US Social Security website [here][5]). These can either be directly downloaded to your server instance, or - if you have them locally and wish to send them to your AWS instance, you can do so using `scp`:

```
scp -r -i <.PEM KEY LOCATION ON LOCAL COMPUTER> names/ <USERNAME REMOTE>@<IP ADDRESS REMOTE>:/path/to/project-directory/
```

Which assumes they are held locally in a folder 'names' (within current directory), and requires the location on your local computer of your SSH public key .pem file. Celebrodisiac looks for these files in a directory called <project-directory>/names, but you can use another directory if you change the relevant environment variable in the babyMakers.cfg file (see below).


## Troubleshooting and logging

Should you face inexplicable problems getting this to run, the most important thing to do is *not pull your hair out* (it might not grow back). A good first step is to setup logging and study the log-files. Here's how to setup logging for python, uWSGI and the upstart file. It is also possible to check NGINX log-files (see here for information).

### python logging
python has a `logging` module. To log errors etc... from (for example) `controller.py` insert the following code into the file:

```
import logging

logging.basicConfig(level=logging.DEBUG, filename='/path-to-log-file/python_log.log')
```
It is also possible to insert log calls (analogous to `print` with `stdout`). See [here][6] for more information.

Also of use is the `pdb` debugging module, which (in lieu of unnecessarily installing `ipython` on the server) can allow investigation of error stacks.

### uWSGI logging

There are several ways to log with uWSGI. The most useful is to add the `--logto /path-to-log-file/uwsgi_log.log` switch to the call to uWSGI made in the script within our upstart file. So that in place of our normal uWSGI call there we have:

```
uwsgi --ini /path/to/project-directory/babyMakers.ini #--logto /path-to-log-file/log/uwsgi_log.out
```

It's also possible to manually start uWSGI from the command line and have it serve on a test port (typically 8000). Doing this with the following command runs uWSGI as a process, so that output is logged directly to `stdout` on the screen:

```
uwsgi --socket 0.0.0.0:8000 --protocol=http -w wsgi
```

Alternatively we can run uWSGI as a daemon using the `--daemonize` switch, which also allows us to pass a path for logging to file:

```
uwsgi --socket 0.0.0.0:8000 --protocol=http -w wsgi --daemonize /path-to-log-file/uwsgi_log.log
```
In this case, we should make sure to kill the uWSGI daemon (toughness: 12) by finding its PID from `ps aux` and then using `kill <PID>`.

### upstart logging

An upstart job can be made to log by adding the line `console log` near the top of the `.conf` file. This will cause it to log output (including `echo` statements from within script blocks) to `/var/log/upstart/<conf-filename>.log`. It's often useful to use `tail -f <log-file>` to view the most recently written lines in potentially large log files.

<!-- How to SCP onto remote machine (note from terminal on local machine, not from existing ssh session):

scp -r -i <.PEM KEY LOCATION ON LOCAL COMPUTER> names/ <USERNAME REMOTE>@<IP ADDRESS REMOTE>:/home/ubuntu/babyMakers/

Note that the -i switch is for locating the public key and was crucial! -->


<!-- Instructions for PostgreSQL on ubuntu: https://help.ubuntu.com/community/PostgreSQL -->

<!-- To start off, we need to set the password of the PostgreSQL user (role) called "postgres"; we will not be able to access the server externally otherwise. As the local “postgres” Linux user, we are allowed to connect and manipulate the server using the psql command.

In a terminal, type:


sudo -u postgres psql postgres
this connects as a role with same name as the local user, i.e. "postgres", to the database called "postgres" (1st argument to psql).

Set a password for the "postgres" database role using the command:

\password postgres
and give your password when prompted. The password text will be hidden from the console for security purposes.

Type Control+D or \q to exit the posgreSQL prompt. -->




[1]: http://upstart.ubuntu.com/getting-started.html
[2]: http://stackoverflow.com/questions/14904142/export-variables-defined-in-another-file
[3]: https://www.digitalocean.com/community/tutorials/how-to-read-and-set-environmental-and-shell-variables-on-a-linux-vps
[4]: http://www.postgresql.org/docs/9.3/static/app-psql.html
[5]: https://www.ssa.gov/oact/babynames/limits.html
[6]: https://docs.python.org/2/howto/logging.html
[7]: https://www.nginx.com/resources/wiki/start/topics/tutorials/install/
[8]: http://www.celebrodisiac.com/

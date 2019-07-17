# Local Development Guide

Get a local development version of Puzzle Massive to run on your machine by
following these (super awesome) instructions. This is necessary in order to
create a dist file (`make dist`) for deploying to a production server.

Written for a Linux machine that is Debian based.  Only tested on Ubuntu.  Use
 [VirtualBox](https://www.virtualbox.org/) and
 [Vagrant](https://www.vagrantup.com/) if not on a Linux machine.  Initialize or
 update the `Vagrantfile` with `bento/ubuntu-18.04`.

This guide assumes some familiarity with using the terminal and administrating
a linux based machine like Ubuntu.  If something isn't working right or you get
stuck, please reach out on the Discord chat channels for the project.

A Vagrant box is available that has already been set up with some puzzles
and such.  Please follow the [Quick start guide](quickstart.md) to get
a virtual machine up which will use the included `Vagrantfile`.

## Initial setup

After cloning or forking the git repo
[puzzle-massive](https://github.com/jkenlooper/puzzle-massive); open a terminal
and `cd` to that directory.

If using Vagrant; then run `vagrant up` after switching the box back to the
ubuntu version in the `Vagrantfile` and ssh in (`vagrant ssh`) and go to
the /vagrant/ shared directory when running the rest of the commands.

If using Vagrant and VirtualBox then edit Vagrantfile to switch the box to
ubuntu version first and enable the provisioning scripts.

```bash
vagrant up;
vagrant ssh;

# After logging in as the vagrant user on the vagrant machine.
cd /vagrant/;

# The /vagrant/ directory is a shared folder with the host machine.
ls;
```

If **not** using Vagrant and running locally on a Ubuntu 18.04 (Bionic Beaver)
machine:

```bash
# Run only some commands from bin/init.sh to create the 'dev' user:
sudo adduser dev
# Set the user to have sudo privileges by placing in the sudo group
sudo usermod -aG sudo dev
```

Run the initial `bin/setup.sh` script after logging into the development
machine.

```bash
# Install other software dependencies with apt-get and npm.
sudo ./bin/setup.sh;
```

To have TLS (SSL) on your development machine run the `bin/provision-local.sh`
script. That will use `openssl` to create some certs in the web/ directory.
The rootCA.pem should be imported to Keychain Access and marked as always trusted.
*This step is not necessary.  The site isn't using https yet.*

### The 'dev' user and sqlite db file

The sqlite db file is owned by dev with group dev.  If developing with
a different user then run `adduser nameofuser dev` to include the 'nameofuser'
to the dev group.  Make sure to be signed in as the dev user when manually
modifying the database.

If using Vagrant then change the password for dev user and login as that user
when doing anything with the sqlite db file.  Any other commands that modify the
source files and such should be done as the vagrant user (default user when
using `vagrant ssh`).

```bash
sudo passwd dev;
su dev;
```

## Configuration with `.env`

Create the `.env` and `.htpasswd` files.  These should **not** be added to the
distribution or to source control (git).

```bash
touch .env;
touch .htpasswd;
```

It is recommended to set up an account on [Unsplash](https://unsplash.com/).  An
app will need to be created in order to get the application id and such.  See
[Unsplash Image API](https://unsplash.com/developers).  Leave blank if not using
images from Unsplash.

```bash
echo "UNSPLASH_APPLICATION_ID=" >> .env;
echo "UNSPLASH_APPLICATION_NAME=" >> .env;
echo "UNSPLASH_SECRET=" >> .env;
```

Set these to something unique for the app.  The NEW_PUZZLE_CONTRIB sets the URL
used for directly submitting photos for puzzles.  Eventually the puzzle
contributor stuff will be done, but for now set it to your favorite [Muppet character](https://en.wikipedia.org/wiki/List_of_Muppets).

```bash
echo "NEW_PUZZLE_CONTRIB=beaker" >> .env;
echo "SECURE_COOKIE_SECRET=make-up-some-random-text" >> .env;
```

These are mostly optional and self explanatory.  Email settings are for
transactional emails and currently only used when a photo for a puzzle is
suggested.  If hosting a production version of the site is planned, then set the
domain name to something other then puzzle.massive.xyz.  Leave it with the
default if only doing local development on your own machine.

```bash
echo "SUGGEST_IMAGE_LINK='https://any-website-for-uploading/'" >> .env;
echo "SMTP_HOST='localhost'" >> .env;
echo "SMTP_PORT='587'" >> .env;
echo "SMTP_USER='user@localhost'" >> .env;
echo "SMTP_PASSWORD='somepassword'" >> .env;
echo "EMAIL_SENDER='sender@localhost'" >> .env;
echo "EMAIL_MODERATOR='moderator@localhost'" >> .env;
echo "DOMAIN_NAME='puzzle.massive.xyz'" >> .env;
```

The admin page uses basic auth.  Note that this site is not configured to use
a secure protocol (https) and so anyone on your network _could_ see the password
used here.  Not really a big deal, but for production deployments the nginx
config is also set to deny any requests to the admin page if not originating
from the internal IP.  Admin page access for production requires using a proxy
or changing the nginx config.

Set the initial admin user and password.  This file is copied to the
/srv/puzzle-massive/ when installing with `make install`.

```bash
htpasswd -c .htpasswd admin;
```

## Setup For Building

The website apps are managed as 
[systemd](https://freedesktop.org/wiki/Software/systemd/) services.
The service config files are created by running `make` and installed with 
`sudo make install`.  It is recommended to use Python's `virtualenv .`
and activating each time for a new shell with `source bin/activate` before
running `make`.

**All commands are run from the projects directory unless otherwise noted.**  For
the Vagrant setup this is the shared folder `/vagrant/`.

```bash
vagrant ssh;
cd /vagrant/;
```

If `nvm` isn't available on the dev machine then install it.  See
[github.com/creationix/nvm](https://github.com/creationix/nvm) for more
information.

Note that the `bin/setup.sh` script uses a system installed `npm` in order to
install `svgo`. The `svgo` command is used by the puzzle piece renderer process.
When installing `nvm`, it may show a warning about `svgo` when switching to
a different Node version.  This warning can be ignored since development doesn't
use `svgo`.

```bash
# Install Node Version Manager
curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.34.0/install.sh | bash
source ~/.bashrc

# Install latest Nodejs LTS version and set it in the .nvmrc
nvm install --lts=Dubnium
nvm current > .nvmrc

# Install and use the version set in .nvmrc
nvm install
nvm use
```

When first installing on a development machine (not production) run:

```bash
# Setup to use a virtual python environment
virtualenv . -p python3;
source bin/activate;

# Build the dist files for local development
npm install;
npm run build;

# Makes the initial development version and the db.dump.sql file
make;

# Creates the initial database from the db.dump.sql file, installs other files
sudo make install;

# Create the puzzle database tables and initial data
# As the dev user:
sudo su dev
source bin/activate
python api/api/create_database.py site.cfg;
exit

sudo systemctl reload nginx
```

The puzzle site is available on your own machine at http://localhost or
http://localhost:8080 if using Vagrant.

Update `/etc/hosts` to have local-puzzle-massive map to your machine.  Access your
local development version of Puzzle Massive at http://local-puzzle-massive/ .
**If using vagrant you'll need to use the 8080 port http://local-puzzle-massive:8080/ .**

Append to your `/etc/hosts` file on the host machine (Not vagrant).  The
location of this file on a Windows machine is different.

```bash
# Append to /etc/hosts
127.0.0.1 local-puzzle-massive
```

## Developing Puzzle Massive locally and creating puzzles

Update the URLs shown to use port 8080 if using Vagrant.

After the initial install of Puzzle Massive on your machine there won't be any
puzzles yet.  You'll need to create one (create two to avoid a bug when only one
is available) by visiting the super secret URL for directly creating new
puzzles: 
http://local-puzzle-massive/chill/site/new-puzzle/[NEW_PUZZLE_CONTRIB]/

After creating some new puzzles, the next step is to moderate them and start
the rendering process.  That can be accomplished by logging into the admin side:
http://local-puzzle-massive/chill/site/admin/puzzle/ . This admin UI is super
clunky and has a lot of room for improvement.  You'll need to batch edit the
submitted puzzles to be approved and then click on render.

### Building the `dist/` files

The javascript and CSS files in the `dist/` directory are built from the source
files in `src/` by running the `npm run build` command.  This uses
[webpack](https://webpack.js.org/) and is configured with the
`webpack.config.js`.  The entry file is `src/index.ts` and following that the
main site bundle (`site.bundle.js`, `site.css`) is built from
`src/site/index.js`.

The source files for javascript and CSS are organized mostly as components.  The
`src/site/` being an exception as it includes CSS and javascript used across the
whole site. Each component includes its own CSS (if applicable) and the CSS
classes follow the 
[SUIT CSS naming conventions](https://github.com/suitcss/suit/blob/master/doc/naming-conventions.md).

When editing files in `src/` either run `npm run debug` or `npm run watch`.  The
production version is done with `npm run build` which will create compressed
versions of the files.

## Creating a versioned dist for deployment

After making any changes to the source files; commit those changes to git in
order for them to be included in the distribution file.  The distribution file
is uploaded to the server and the guide to do deployments should then be
followed.

To create the versioned distribution file (like puzzle-massive-2.2.0.tar.gz) use the
`make dist` command.  Note that the version is set in the package.json.

The script to create the distribution file only includes the files that have
been committed to git.  It will also limit these to what is listed in the
`puzzle-massive/MANIFEST`.

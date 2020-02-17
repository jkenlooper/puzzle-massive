# Local Development Guide

Get a local development version of Puzzle Massive to run on your machine by
following these (super awesome) instructions. This is necessary in order to
create a dist file (`make dist`) for deploying to a production server.

Written for a Linux machine that is Debian based. Only tested on Ubuntu 18.04. Use
[VirtualBox](https://www.virtualbox.org/) and
[Vagrant](https://www.vagrantup.com/) if not on a Linux machine.

This guide assumes some familiarity with using the terminal and administrating
a linux based machine like Ubuntu. If something isn't working right or you get
stuck, please reach out on the
[Discord chat channels](https://discord.gg/uVhE2Kd)
for the project.

## Initial setup

After cloning or forking the git repo
[puzzle-massive](https://github.com/jkenlooper/puzzle-massive); open a terminal
and `cd` to that directory.

If using Vagrant; then run `vagrant up` after switching the box back to the
ubuntu version in the `Vagrantfile` and ssh in (`vagrant ssh`) and clone go to
the /vagrant/ shared directory when running the rest of the commands.

If using Vagrant and VirtualBox, then it is recommended to not do development on
a shared folder and instead create a dev user and clone from the shared
/vagrant/ folder. This avoids potential weird issues when using a shared folder
between VirtualBox and your host machine. The repo should be cloned from the
shared /vagrant folder to the /home/dev/puzzle-massive folder in the virtual
machine.

```bash
vagrant up;
vagrant ssh;

# After logging in as the vagrant user on the vagrant machine.
# Switch to the dev user.
# and clone the repo from the shared vagrant folder.
sudo su dev;
cd;
git clone /vagrant/ puzzle-massive;
cd puzzle-massive;
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
machine. This may take some time and it will ask a few questions.

```bash
# Install other software dependencies with apt-get and npm.
sudo ./bin/setup.sh;

# Fix permissions on home .config and .npm directories because of sudo npm
# install command used in setup.sh script.
sudo chown -R dev:dev ~/.config
sudo chown -R dev:dev ~/.npm
```

To have TLS (SSL) on your development machine run the `bin/provision-local.sh`
script. That will use `openssl` to create some certs in the web/ directory. The
`local-puzzle-massive-CA.pem`
file should be imported to Keychain Access and marked as always trusted.
_This step is not necessary. The site isn't using https yet._

### The 'dev' user and sqlite db file

The sqlite db file is owned by dev with group dev. If developing with
a different user then run `adduser nameofuser dev` to include the 'nameofuser'
to the dev group. Make sure to be signed in as the dev user when manually
modifying the database.

```bash
sudo su dev;
```

## Configuration with `.env`

Create the `.env` and `.htpasswd` files. These should **not** be added to the
distribution or to source control (git).

```bash
touch .env;
touch .htpasswd;
```

It is recommended to set up an account on [Unsplash](https://unsplash.com/). An
app will need to be created in order to get the application id and such. See
[Unsplash Image API](https://unsplash.com/developers). Leave blank if not using
images from Unsplash.

```bash
echo "UNSPLASH_APPLICATION_ID=" >> .env;
echo "UNSPLASH_APPLICATION_NAME=" >> .env;
echo "UNSPLASH_SECRET=" >> .env;
```

Set these to something unique for the app. The NEW_PUZZLE_CONTRIB sets the URL
used for directly submitting photos for puzzles. Eventually the puzzle
contributor stuff will be done, but for now set it to your favorite [Muppet character](https://en.wikipedia.org/wiki/List_of_Muppets).

```bash
echo "NEW_PUZZLE_CONTRIB=beaker" >> .env;
echo "SECURE_COOKIE_SECRET=make-up-some-random-text" >> .env;
```

These are mostly optional and self explanatory. Email settings are for
transactional emails and currently only used when a photo for a puzzle is
suggested. If hosting a production version of the site is planned, then set the
domain name to something other then puzzle.massive.xyz. Leave it with the
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

The admin page uses basic auth. Note that this site is not configured to use
a secure protocol (https) and so anyone on your network _could_ see the password
used here. Not really a big deal, but for production deployments the nginx
config is also set to deny any requests to the admin page if not originating
from the internal IP. Admin page access for production requires using a proxy
or changing the nginx config.

Set the initial admin user and password. This file is copied to the
/srv/puzzle-massive/ when installing with `make install`.

```bash
htpasswd -c .htpasswd admin;
```

## Setup For Building

The website apps are managed as
[systemd](https://freedesktop.org/wiki/Software/systemd/) services.
The service config files are created by running `make` and installed with
`sudo make install`. It is recommended to use Python's `virtualenv .`
and activating each time for a new shell with `source bin/activate` before
running `make`.

**All commands are run from the projects directory unless otherwise noted.** For
the Vagrant setup this should be the home folder of the dev user
`/home/dev/puzzle-massive/`.

```bash
vagrant ssh;
sudo su dev;
cd /home/dev/puzzle-massive/;
```

Some git commit hooks are installed and rely on commands to be installed to
format the python code ([black](https://github.com/python/black)) and format other code ([prettier](https://github.com/prettier/prettier)). Committing
before following the below setup that installs these will result in an error.

The [Node Version Manager (nvm)](https://github.com/creationix/nvm) is used in
order to select a npm and node version that is compatible with the build
scripts. See the link for more information.

```bash
# On Vagrant or dev machine
# Install Node Version Manager (nvm)
curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.34.0/install.sh | bash

# Install and use the version set in .nvmrc
nvm install
nvm use
```

When first installing on a development machine (not production) run:

```bash
# Setup to use a virtual python environment
virtualenv . -p python3;
source bin/activate;

# Install black to format python code when developing
pip install black;

# Build the dist files for local development
nvm use
npm install;
npm run build;

# Makes the initial development version and the db.dump.sql file
make;

# Creates the initial database from the db.dump.sql file, installs other files
sudo make install;

# Update the limits in /etc/ImageMagick-6/policy.xml
# Refer to notes in api/api/jobs/pieceRenderer.py

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

Update `/etc/hosts` to have local-puzzle-massive map to your machine. Access your
local development version of Puzzle Massive at http://local-puzzle-massive/ .
**If using vagrant you'll need to use the 8080 port http://local-puzzle-massive:8080/ .**

Append to your `/etc/hosts` file on the host machine (Not vagrant). The
location of this file on a Windows machine is different.

```bash
# Append to /etc/hosts
127.0.0.1 local-puzzle-massive
```

## Developing Puzzle Massive locally and creating puzzles

Update the URLs shown to use port 8080 if using Vagrant.

After the initial install of Puzzle Massive on your machine there won't be any
puzzles yet. You'll need to create one (create two to avoid a bug when only one
is available) by visiting the super secret URL for directly creating new
puzzles:
http://local-puzzle-massive/chill/site/new-puzzle/[NEW_PUZZLE_CONTRIB]/

After creating some new puzzles, the next step is to moderate them and start
the rendering process. That can be accomplished by logging into the admin side:
http://local-puzzle-massive/chill/site/admin/puzzle/ . This admin UI is super
clunky and has a lot of room for improvement. You'll need to batch edit the
submitted puzzles to be approved and then click on render.

### Creating random puzzles and players for testing

A script to generate a variety of puzzles and player data is used when
developing to better simulate conditions on a production version. Run this
script as needed. Some examples to get started are shown here.

```bash
puzzle-massive-testdata players --count=100;

puzzle-massive-testdata puzzles --count=10 --min-pieces=200 --pieces=900 --size=1800x1300\!;
puzzle-massive-testdata puzzles --count=10 --min-pieces=200 --pieces=900 --size=800x1500\!;
puzzle-massive-testdata puzzles --count=1 --pieces=2000 --size=3800x3500\!;
puzzle-massive-testdata puzzles --count=300 --min-pieces=9 --pieces=200 --size=180x180\!;

puzzle-massive-testdata instances --count=10 --min-pieces=200 --pieces=500;
```

### Building the `dist/` files

The javascript and CSS files in the `dist/` directory are built from the source
files in `src/` by running the `npm run build` command. This uses
[webpack](https://webpack.js.org/) and is configured with the
`webpack.config.js`. The entry file is `src/index.ts` and following that the
main site bundle (`site.bundle.js`, `site.css`) is built from
`src/site/index.js`.

The source files for javascript and CSS are organized mostly as components. The
`src/site/` being an exception as it includes CSS and javascript used across the
whole site. Each component includes its own CSS (if applicable) and the CSS
classes follow the
[SUIT CSS naming conventions](https://github.com/suitcss/suit/blob/master/doc/naming-conventions.md).

When editing files in `src/` either run `npm run debug` or `npm run watch`. The
production version is done with `npm run build` which will create compressed
versions of the files.

## Creating a versioned dist for deployment

After making any changes to the source files; commit those changes to git in
order for them to be included in the distribution file. The distribution file
is uploaded to the server and the guide to do deployments should then be
followed.

To create the versioned distribution file (like puzzle-massive-2.2.0.tar.gz) use the
`make dist` command. Note that the version is set in the package.json.

The script to create the distribution file only includes the files that have
been committed to git. It will also limit these to what is listed in the
`puzzle-massive/MANIFEST`.

## Feature branches and chill-data

The `chill-data.sql` contains only a dump of the database tables that are used
in chill. The Chill, Node, Node_Node, Query, Route, and Template tables are
rebuilt if the `cat chill-data.sql | sqlite3 /path/to/sqlite/db` command is run.
This command is commonly run when deploying or setting up the puzzle on
a machine. A new feature on a git feature branch will sometimes require updates
to the `chill-data.sql` file. There is a potential that if multiple feature
branches are being developed, that there will be messy git conflicts in
`chill-data.sql`. That would happen if those feature branches committed any
changes to `chill-data.sql`.

To solve this potential problem of conflicts with `chill-data.sql`, feature
branches should _not_ be committing any changes to the `chill-data.sql`.
Instead the new additions to the chill data should be dumped into
a `chill-data-feature-[feature-name].yaml` file using the `chill dump` command.
Then when the feature branch is being merged into the develop branch,
the chill feature yaml can also be merged into the `chill-data.yaml`

The `chill-data-feature-[feature-name].yaml` file should also be edited to
_only_ include changes that are being added for that feature branch.

On updates to any chill-data\*.yaml files; run the below commands to reload the chill database.

```bash
# stop the apps first
sudo ./bin/puzzlectl.sh stop;

# Builds new db.dump.sql
make;

# Reset the chill data tables with what is in the new db.dump.sql file
sqlite3 "/var/lib/puzzle-massive/sqlite3/db" < db.dump.sql;
echo "pragma journal_mode=wal" | sqlite3 /var/lib/puzzle-massive/sqlite3/db;
```

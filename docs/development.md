# Local Development Guide

Get a local development version of Puzzle Massive to run on your machine by
following these (super awesome) instructions. This is necessary in order to
create a dist file (`make dist`) for deploying to a production server.

Written for a Linux machine that is Debian based.  Only tested on Ubuntu.  Use
 [VirtualBox](https://www.virtualbox.org/) and
 [Vagrant](https://www.vagrantup.com/) or something similar if not on a Linux
 machine.

If using Vagrant; then run `vagrant up` and ssh in (`vagrant ssh`) and go to
the /vagrant/ shared directory when running the rest of the commands.

Run the `bin/init.sh` script to configure the server with ssh and a user if
needed.  Don't need to run this if using Vagrant.

The `bin/setup.sh` is used to install dependencies for the server.  It is
automatically run when provisioning a Vagrant machine.

To have TLS (SSL) on your development machine run the `bin/provision-local.sh`
script. That will use `openssl` to create some certs in the web/ directory.
The rootCA.pem should be imported to Keychain Access and marked as always trusted.
*This step is not necessary.  The site isn't using https yet.*

The website apps are managed as 
[systemd](https://freedesktop.org/wiki/Software/systemd/) services.
The service config files are created by running `make` and installed with 
`sudo make install`.  It is recommended to use Python's `virtualenv .`
and activating each time for a new shell with `source bin/activate` before
running `make`.

The db file is owned by dev with group dev.  If developing with
a different user then run `adduser nameofuser dev` to include the 'nameofuser'
to the dev group.

If using Vagrant then change the password for dev user and login as that user.

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

If `nvm` isn't available on the dev machine then install it.  See [github.com/creationix/nvm](https://github.com/creationix/nvm) for more information.

```bash
# Install Node Version Manager
curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.34.0/install.sh | bash
source ~/.bashrc
nvm install v10.15.0
nvm use
```

When first installing on the dev machine run:

```bash
# Setup to use a virtual python environment
virtualenv .;
source bin/activate;

# Makes the initial development version
make;
cp chill-data.sql db.dump.sql;

# Build the dist files for local development
(
cd puzzle-pieces;
npm install;
npm link;
)
npm link puzzle-pieces;
npm install;
npm run build;

sudo make install;

# As the dev user:
sudo su dev
source bin/activate
python api/api/create_database.py site.cfg;
exit

sudo systemctl reload nginx
```

Set the credentials to use a compatible s3 setup with either the awscli or
manually adding the credentials.  At this time it is only for migrating old puzzle
files.  New development isn't using any AWS services anymore as it isn't needed
for the project at this time.

```bash
# As the dev user:
pip install awscli
aws configure
```

Update `/etc/hosts` to have local-puzzle-massive map to your machine.  Access your
local development version of Puzzle Massive at http://local-puzzle-massive/ .
If using vagrant you'll need to use the 8080 port http://local-puzzle-massive:8080/ .

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

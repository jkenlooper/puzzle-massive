# Local Development Guide

Get a local development version of Puzzle Massive to run on your machine by
following these (super awesome) instructions. This is necessary in order to
create a dist file (`make dist`) for deploying to a production server.

Written for a Linux machine that is Debian based. Only tested on
[Ubuntu 18.04.4 LTS (Bionic Beaver)](http://releases.ubuntu.com/18.04/).
It is recommended to use a virtual machine of some sort to keep dependencies for
the Puzzle Massive services isolated and manageable. Some virtualization
software suggestions are listed below.

- [VirtualBox](https://www.virtualbox.org/) - can be used with Vagrant.
- [Vagrant](https://www.vagrantup.com/) - a Vagrantfile has already been made.
- [KVM](https://wiki.debian.org/KVM) - Kernel Virtual Machine is available for
  Linux machines.

This guide assumes some familiarity with using the terminal and administrating
a Linux based machine like Ubuntu. If something isn't working right, or you get
stuck, please reach out on the
[Discord chat channels](https://discord.gg/uVhE2Kd)
for the project.

## Initial setup

After cloning or forking the git repo
[puzzle-massive](https://github.com/jkenlooper/puzzle-massive); open a terminal
and `cd` to that directory.

Development can be done with any text editor or IDE that you are comfortable
with. If using a virtual machine; then the files will either need to be edited
on the virtual machine or copied over each time they change. The
`bin/devsync.sh`
script helps with copying files to the virtual machine.
TODO: A service can be enabled on the virtual machine that will trigger any
builds necessary when any source files get updated.

The instructions shown here assume that you are logged into a Linux system
(`uname -o`) and are running Ubuntu 18 (`lsb_release -a`).

### Create `dev` user

Create the `dev` user for Puzzle Massive. This user will own the sqlite database
among other things. There are other commands that set up ssh and adds your
public key to your virtual machine. See the bin/init.sh for that if you are
using a virtual machine.

```bash
# Run only some commands from bin/init.sh to create the 'dev' user:
sudo adduser dev
# Set the user to have sudo privileges by placing in the sudo group
sudo usermod -aG sudo dev
```

### Install dependencies

Run the initial setup script that will install many of the dependencies with
apt-get the Debian based package manager. The redis config is also updated to
set maxmemory when running the setup.sh script.

```bash
# Install other software dependencies with apt-get and npm.
sudo ./bin/setup.sh;

# Fix permissions on home .config and .npm directories because of sudo npm
# install command used in setup.sh script.
sudo chown -R dev:dev ~/.config
sudo chown -R dev:dev ~/.npm
```

### Create local SSL certs (optional)

To have TLS (SSL) on your development machine run the
`provision-local-ssl-certs.sh` script. That will use `openssl` to create some
certs in the web/ directory. The `localhost-CA.pem` file that is created in the
home directory by default should be imported to Keychain Access and marked as
always trusted. The Firefox web browser will require importing the
`localhost-CA.pem` certificate authority file.

```bash
./bin/provision-local-ssl-certs.sh
```

### Create the `.env` and `.htpasswd` files

Use the `devsetup.sh` to create the `.env` and `.htpasswd` files. These should
**not** be added to the distribution or to source control (git). Edit them as
needed for your use case.

```bash
# Creates the .env and .htpasswd files.
./bin/devsetup.sh;
```

## Setup For Building

The website apps are managed as
[systemd](https://freedesktop.org/wiki/Software/systemd/) services.
The service config files are created by running `make` and installed with
`sudo make install`. It is recommended to use Python's `virtualenv . -p python3`
and activating each time for a new shell with `source bin/activate` before
running `make`.

**All commands are run from the project's directory unless otherwise noted.**

Some git commit hooks are installed and rely on commands to be installed to
format the python code (black) and format other code (prettier). Committing
before following the below setup will result in an error if these commands
haven't been installed on the development machine.

### Install `nvm`

If `nvm` isn't available on the dev machine then install it. See
[github.com/nvm-sh/nvm](https://github.com/nvm-sh/nvm) for more
information.

```bash
# Install Node Version Manager

curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.35.2/install.sh | bash
source ~/.bashrc

# Install and use the version set in .nvmrc
nvm install
nvm use
```

### Initializing the project

The limits for ImageMagick may need to be updated. Manually edit the
`/etc/ImageMagick-6/policy.xml` file on your development machine. Refer to notes
in `[api/api/jobs/pieceRenderer.py](api/api/jobs/pieceRenderer.py)` about what
settings to use.

When first installing on a development machine run the below commands.

```bash
# Setup to use a virtual python environment
virtualenv . -p python3;
source bin/activate;

# Install black to format python code when developing
pip install black;

# Build the dist files for local development
nvm use
npm install;

# Checkout any git submodules in this repo if didn't
# `git clone --recurse-submodules ...`.
git submodule init;
git submodule update;

# Build the dist files for local development
npm run build;

# Makes the initial development version
make;

sudo make install;
sudo ./bin/appctl.sh stop;

# Create the puzzle database tables and initial data
# As the dev user:
sudo su dev
source bin/activate
python api/api/create_database.py site.cfg;
exit

sudo systemctl reload nginx;
sudo ./bin/appctl.sh start;
```

### Set local-puzzle-massive hostname

Update `/etc/hosts` to have local-puzzle-massive map to your machine.
Access your local development version of the website at
http://local-puzzle-massive/ . If using vagrant you'll need to use the
8080 port http://local-puzzle-massive:8080/ . There are also some issues when
using a port on the local-puzzle-massive host and the website does a redirect.

Append "127.0.0.1 local-puzzle-massive" to your `/etc/hosts` file on the host
machine (not the virtual machine). You'll then be able to access your local
version of the site at the http://local-puzzle-massive/ URL. If installed on
a virtual machine; then change the 127.0.0.1 to that IP of the virtual machine.
This IP can be found by logging into the virtual machine and using this command:
`ip -4 -br addr show`

```bash
echo "127.0.0.1 local-puzzle-massive" >> /etc/hosts
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

### Python Unit Tests

Some unit tests exist to cover parts of the api application. Some older tests
have been skipped since they were not actively maintained. The existing ones can
be run with the following commands.

```bash
# Run all the tests for the api
python -m unittest discover --start-directory api --failfast

# Run specific tests
python api/api/test_puzzle_details.py

# Run specific test case
python api/api/test_puzzle_details.py TestInternalPuzzleDetailsView.test_missing_payload
```

### Building the `dist/` files

The javascript and CSS files in the `dist/` directory are built from the source
files in `src/` by running the `npm run build` command. This uses
[webpack](https://webpack.js.org/) and is configured with the
`webpack.config.js`. The entry file is `src/index.js` and following that the
main app bundle (`app.bundle.js`, `app.css`) is built from
`src/app.js`.

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

To create the versioned distribution file (like `puzzle-massive-2.0.0.tar.gz`) use the
`make dist` command. Note that the version is set in the `package.json`.

The script to create the distribution file only includes the files that have
been committed to git. It will also limit these to what is listed in the
`MANIFEST`.

## Committing database data to source control

Any data that is required for the site to operate should be stored along with
the source files. Chill specific data is stored as `chill-data.yaml` and any
other `chill-data-*.yaml` files. Other data that chill would query for should be
stored in a `site-data.sql` file. The `bin/create-site-data-sql.sh` can be
edited and run when needed in development. It should export database table data
to the `site-data.sql` file. The `site-data.sql` should be committed to source
control and will be used when deploying the site to a server.

The `chill-data.yaml` and `chill-data-*.yaml` files can be manually edited or
recreated by running the `chill dump` command. The dump command will export
chill specific data to these files.

It is good practice to dump feature branch specific chill data to separate files
like `chill-data-[feature-name].yaml`. That way those changes will not conflict
with other changes that may be committed to `chill-data.yaml`. When the feature
branch has been merged to the develop branch, the
`chill-data-feature-[feature-name].yaml` file contents should be appended to the
`chill-data.yaml` file. The `chill-data-feature-[feature-name].yaml` file should
then be removed.

The `chill-data-feature-[feature-name].yaml` file should also be edited to
_only_ include changes that are being added for that feature branch.

On updates to any `chill-data*.yaml` or `site-data.sql` files; run the below
commands to reload the chill database.

```bash
# stop the apps first
sudo ./bin/appctl.sh stop;

# Builds new db.dump.sql
make;

# Update the database with what is in db.dump.sql
sudo make install;
```

## Uninstalling the app

Run the below commands to remove puzzle-massive from your
development machine. This will uninstall and disable the services, remove any
files installed outside of the project's directory including the sqlite3
database. _Only do this on a development machine if it's database and other
data is no longer needed._

```bash
source bin/activate;
sudo ./bin/appctl.sh stop;

# Removes any installed files outside of the project
sudo make uninstall;

# Remove files generated by make
make clean;
deactivate;

# Remove any source files and directories that are ignored by git...
# Swap -n for -f for deleting files
git clean -dX -n

# ...or just clean up and preserve some files.
# Swap -n for -f for deleting files
git clean -dx -e /.htpasswd -e /.env -e /.has-certs -e /web -n

# Removes all data including the sqlite3 database
sudo rm -rf /var/lib/puzzle-massive/
```

## Regenerating with cookiecutter

Get the latest changes from the cookiecutter that initially generated the
project
([jkenlooper/cookiecutter-website](https://github.com/jkenlooper/cookiecutter-website))
by uninstalling the app, running the cookiecutter in a different directory, and
then rsync the changed files back in. Use `git` to then patch files as needed.

```bash
now=$(date --iso-8601 --utc)
# In the project directory of puzzle-massive.
cd ../;
mkdir puzzle-massive--${now};
cd puzzle-massive--${now};

# Regenerate using last entered config from initial project.  Then git clean the
# new project files that were just created.
cookiecutter \
  --config-file ../puzzle-massive/.cookiecutter-regen-config.yaml \
  gh:jkenlooper/cookiecutter-website renow=${now};
cd puzzle-massive;
git clean -fdx;

# Back to parent directory
cd ../../;

# Create backup tar of project directory before removing all untracked files.
tar --auto-compress --create --file puzzle-massive-${now}.bak.tar.gz puzzle-massive;
cd puzzle-massive;
git clean -fdx --exclude=.env --exclude=.htpasswd;
cd ../;

# Use rsync to copy over the generated project
# (puzzle-massive--${now}/puzzle-massive)
# files to the initial project.
# This will delete all files from the initial project.
rsync -a \
  --itemize-changes \
  --delete \
  --exclude=.git/ \
  --exclude=.env \
  --exclude=.htpasswd \
  puzzle-massive--${now}/puzzle-massive/ \
  puzzle-massive

# Remove the generated project after it has been rsynced.
rm -rf puzzle-massive--${now};

# Patch files (git add) and drop changes (git checkout) as needed.
# Refer to the backup puzzle-massive-${now}.bak.tar.gz
# if a file or directory that was not tracked by git is missing.
cd puzzle-massive;
git add -i .;
git checkout -p .;
```

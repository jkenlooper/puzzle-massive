# Local Development Guide

Get a **local development** version of Puzzle Massive to run on your machine by
following this guide. You'll need to install the below software in order to
create a virtual machine.

- [VirtualBox](https://www.virtualbox.org/)
- [Vagrant](https://www.vagrantup.com/)

Some definitions that this guide uses:

<dl>
  <dt>local machine</dt>
  <dd>
  This is your own computer (localhost) that you edit source files on using your
  text editor or IDE of choice. This will be the machine that VirtualBox and
  Vagrant have been installed on.
  </dd>
  <dt>development machine or virtual machine</dt>
  <dd>
  The Ubuntu machine that will be setup to run the Puzzle Massive services.
  Source files will be uploaded to it from the local machine each time they
  change. This machine is automatically created when running the `vagrant up`
  command and will have the Puzzle Massive instance running on
  http://localhost:8080 or another port if that one has already been taken.
  </dd>
</dl>

This guide assumes some familiarity with using the terminal. If something isn't
working right, or you get stuck, please reach out on the
[Discord chat channels](https://discord.gg/uVhE2Kd)
for the project.

## Quick setup with vagrant and virtualbox

Running the below vagrant commands _should_ get a local version of Puzzle
Massive working on your own machine.

### Create `.env` Configuration File

The configuration is handled by a `.env` file that is located in the project's
directory. It is recommended to run the
[create_dot_env.sh](../bin/create_dot_env.sh) script in order to create this file.
It will prompt for inputs and show the defaults for each item that can be
configured. This script can be run multiple times and will default to the
choices that you have made before.

It is not required to create a `.env` file if using the vagrant setup. A vagrant
provision script will always be executed that creates this file on the
virtual machine if it doesn't exist on the local machine.

```bash
# Create or update the .env file
./bin/create_dot_env.sh;
```

### Initialize the Vagrant Development Machine

[VirtualBox](https://www.virtualbox.org/) and
[Vagrant](https://www.vagrantup.com/) are used to create a virtual machine on
your local machine. This allows you to run your own version of Puzzle Massive
locally. It is also configured to automatically compile any files changed in
the src/ directory which will then show those changes locally after refreshing
the web browser. The [Vagrantfile](../Vagrantfile) included with the project is for
local development only. It has a few scripts within it that help setup a local
version of Puzzle Massive. This can all be set up by running the below
`vagrant` commands.

```bash
# Bring the virtual machine up and provision it
vagrant up
```

Add an admin user and passphrase which will be used to access the
/chill/site/admin/puzzle/ pages on the site.

```bash
BASIC_AUTH_USER=$(read -p 'username: ' && echo $REPLY) \
BASIC_AUTH_PASSPHRASE=$(read -sp 'passphrase: ' && echo $REPLY) \
vagrant provision --provision-with add-user-to-basic-auth
```

The virtual machine will create a synced folder which is used to copy the files
from this project's directory to a directory on the virtual machine. The
virtual machine will have a 'vagrant' user so the directory that is created for
Puzzle Massive will be at `/home/vagrant/puzzle-massive/`. This folder is only
one-way synced so any changes made in `/home/vagrant/puzzle-massive/` are not
sent back to your project's directory. To copy files to the virtual machine run
the `vagrant rsync` command. A file watcher on the virtual machine will be
triggered when these files change and will start a process to compile the `src/`
files as needed.

```bash
# Copy the files in the project's directory to the virtual machine.
vagrant rsync
```

Now that the project files have been copied over, the rest of the initial setup
can be done. This step to run the provisioning script 'shell-init-dev-local'
should only need to be done once. It creates the initial database and then
starts the services used for Puzzle Massive. These services should then
automatically start up if the virtual machine is rebooted.

The shell-init-dev-local provision script can be run multiple times as needed
since it is idempotent. For example, if the `.env` file has been modified (and
`vagrant rsync` has uploaded it to the virtual machine) then executing this
provisioning script is necessary.

```bash
# Vagrant virtual machine uses this port on the host to forward to the guest.
# Pass along the forwarded port so redirects will work right.
VAGRANT_FORWARDED_PORT_80=$(vagrant port --guest 80) vagrant provision --provision-with shell-init-dev-local
```

### Add Random Puzzles

At this point the site at http://localhost:8080 should be working on your local
machine. It won't have any puzzles or any players initially. To add some
random puzzles to work with and test things run these optional vagrant
provisioning scripts.

These will create some random images and then upload them much like how the
puzzle upload form works. If the site wasn't configured to automatically
approve any submitted puzzles (see AUTO_APPROVE_PUZZLES in the `.env` file),
then you'll need to manually approve these. Go to the admin page to view any
puzzles that have been submitted for approval
http://localhost:8080/chill/site/admin/puzzle/submitted/

```bash
# Optional if needing a few initial puzzles to work with.
vagrant provision --provision-with shell-testdata-puzzles-quick

# Optional if needing lots of puzzles to work with. This may take a few minutes.
vagrant provision --provision-with shell-testdata-puzzles
```

### Edit the Source Code

This project has both server-side code written in mostly Python as well as
client-side code that a web browser uses. All the client-side Javascript, HTML,
and CSS is located in the `src/` directory. After making changes to these files
it will be necessary to copy them over to the virtual machine. This can either
be done with the `vagrant rsync` command to do it once, or you can open another
terminal window and have it always update whenever a change to a file is made
with the `vagrant rsync-auto` command.

```bash
# Copy the files to the virtual machine.
vagrant rsync legacy_puzzle_massive
```

```bash
# Or continually watch files for any changes and copy them to the virtual
# machine.
vagrant rsync-auto legacy_puzzle_massive
```

### Troubleshoot Errors on the Vagrant Virtual Machine

Errors with changing the source code and updating the development machine are
bound to happen. At this time, the logging of errors and such are only
accessible if you ssh into that development machine. Vagrant has a command
for this which is `vagrant ssh`. After logging in you'll see the
`puzzle-massive/` directory at `/home/vagrant/`. This is where all the files
from your project directory are uploaded to. However, this is **not** the
actual files that are used for the running development machine. The actual files
that are being used for the site are in the `/usr/local/src/puzzle-massive/`
directory and are owned by the 'dev' user. Any file changes in `/home/vagrant/puzzle-massive/` will be
automatically copied over to `/usr/local/src/puzzle-massive/` via the
`local-puzzle-massive-auto-devsync` service (assuming that it hasn't failed for
some reason).

```bash
# Log into the virtual machine
vagrant ssh
```

Note that after logging into the development machine as the vagrant user that
there is a 'dev' user. The 'dev' user owns the `/user/local/src/puzzle-massive/`
directory and in order to start and stop the services, or manipulate the
database, you'll need to login as that user. When the 'dev' user was created in
the vagrant provisioning script it set a simple password for the 'dev' user.
You'll be prompted to update the dev user password when logging in. For the
vagrant virtual machine the dev user password is 'vagrant'.

```bash
# Switch to the dev user
sudo su dev
```

#### Errors with Compiling `src/` Files

Any changes to the `src/` files in `/home/vagrant/puzzle-massive/` will trigger
the command `npm run debug` to run. To disable this you can stop the
`local-puzzle-massive-watchit` service. Now you can manually run `npm run debug` and see any errors it might be throwing.

```bash
# Stop the service that automatically runs npm run debug
sudo systemctl stop local-puzzle-massive-watchit

# Now manually run the npm command to see any errors
cd /home/vagrant/puzzle-massive/
npm run debug
```

#### Errors with Python Code

...WIP

#### Errors with Template Code Used in HTML Pages

...WIP

### Maintenance Tasks

Update packages and reboot

```bash
# Requires ansible to be installed.
vagrant provision --provision-with update-packages-and-reboot
```

---

**The below instructions are still relevant if needing to troubleshoot or are
manually setting up without using the above vagrant commands. The "Initial
Setup", and "Setup For Building" sections can be skipped if using vagrant since
most of that was automatically done.**

Written for a Linux machine that is Debian based. Only tested on
[Ubuntu 20.04 LTS (Focal Fossa)](http://releases.ubuntu.com/20.04/).
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

## Set local-puzzle-massive hostname

Update your `/etc/hosts` to have local-puzzle-massive map to your development
machine. This IP can either be localhost (127.0.0.1) or the IP of a virtual
machine. It is recommended that access to this development machine should be
limited so be careful if you use a development machine that is hosted in the
cloud. The local development version of the website will be at
http://local-puzzle-massive/ . If using vagrant for the virtual machine then
you'll need to use the 8080 port http://local-puzzle-massive:8080/ . There are
also some issues when using a port like 8080 on the local-puzzle-massive host
and the website does a redirect.

Append "127.0.0.1 local-puzzle-massive" to your `/etc/hosts` file on the local
machine (not the development machine). You'll then be able to access your local
version of the site at the http://local-puzzle-massive/ URL. If installed on
a virtual machine; then change the 127.0.0.1 to that IP of the virtual machine.
This IP can be found by logging into the virtual machine and using this command:
`ip -4 -br addr show`

```bash
# Update 127.0.0.1 to be the IP of the development machine
echo "127.0.0.1 local-puzzle-massive" >> /etc/hosts
```

## Initial Setup

After cloning or forking the git repo
[puzzle-massive](https://github.com/jkenlooper/puzzle-massive); open a terminal
and `cd` to that directory.

The instructions shown here assume that you are logged into a Linux system
(`uname -o`) and are running Ubuntu (`lsb_release -a`).

### Create `dev` user and project source directory

Use `ssh` to login into the development machine either as root (`ssh root@local-puzzle-massive`) or as a user that has `sudo` permissions.

```bash
ssh local-puzzle-massive;
```

Create the `dev` user for Puzzle Massive. This user will own the sqlite database
among other things. There are other commands that set up ssh and adds your
public key to your virtual machine. See the bin/init.sh for that if you are
using a separate machine (virtual machine) as your development machine.

While logged into the development machine.

```bash
# Run only some commands from bin/init.sh to create the 'dev' user:
sudo adduser dev;
# Set the user to have sudo privileges by placing in the sudo group
sudo usermod -aG sudo dev;
```

Create the initial source directory that files will by `rsync`ed to on the
development machine.

```bash
sudo mkdir -p /usr/local/src/puzzle-massive;
sudo chown dev:dev /usr/local/src/puzzle-massive;
```

Logout (exit) from the development machine. Most of the time this will be
implied in the different sections of this guide.

```bash
# Get back to your local machine by exiting the development machine.
exit;
```

### Add initial files to `/usr/local/src/puzzle-massive`

Development can be done with any text editor or IDE that you are comfortable
with. To better match a production environment the project's source files are
copied over to the /usr/local/src/puzzle-massive/ directory on the development machine.

The `bin/devsync.sh` script is a wrapper around `rsync` that will upload the
source files to the development machine. The destination path is by default
the `/usr/local/src/puzzle-massive/` directory that was created when the dev
user was made.

```bash
# On the local machine
./bin/devsync.sh;
```

### Install dependencies

Should be logged into the development machine

```bash
ssh dev@local-puzzle-massive;
```

Run the initial setup script that will install many of the dependencies with
apt-get the Debian based package manager. The redis config is also updated to
set maxmemory when running the setup.sh script.

```bash
cd /usr/local/src/puzzle-massive/;

# Install other software dependencies with apt-get and npm.
sudo ./bin/setup.sh;
```

### Create local SSL certs (optional)

Should be logged into the development machine

```bash
ssh dev@local-puzzle-massive;
```

To have TLS (SSL) on your development machine run the
`provision-local-ssl-certs.sh` script. That will use `openssl` to create some
certs in the web/ directory. The `localhost-CA.pem` file that is created in the
home directory by default should be imported to Keychain Access and marked as
always trusted. The Firefox web browser will require importing the
`localhost-CA.pem` certificate authority file.

```bash
cd /usr/local/src/puzzle-massive/;
./bin/provision-local-ssl-certs.sh
```

### Create the `.env` file

Use this script to create the `.env` file. The `.env` file should
**not** be added to the distribution or to source control (git). Edit it as
needed for your use case. It should stay within the project's directory.

Run this on the _local machine_ from within the project's directory (use `exit`
command if still logged into development machine).

```bash
# Create or update the .env file
./bin/create_dot_env.sh;
```

## Setup For Building

The website apps are managed as
[systemd](https://freedesktop.org/wiki/Software/systemd/) services.
The service config files are created by running `make` and installed with
`sudo make install`. It is recommended to use Python's `python -m venv .`
and activating each time for a new shell with `source bin/activate` before
running `make`.

Some git commit hooks are installed and rely on commands to be installed to
format the python code (black) and format other code (prettier). Committing
before following the below setup will result in an error if these commands
haven't been installed on the development machine.

### Install `nvm`

If `nvm` isn't available on the local machine then install it. See
[github.com/nvm-sh/nvm](https://github.com/nvm-sh/nvm) for more
information.

Run these on the local machine from within the project's directory.

```bash
# Install Node Version Manager (nvm)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.37.2/install.sh | bash
source ~/.bashrc;

# Install and use the version set in .nvmrc
nvm install;
nvm use;
```

### Initialize the project

On the local machine install dependencies for prettier and black. These tools
are needed to autoformat the changed code before committing.
Create a python virtual environment with `python -m venv .` .

```bash
# Setup to use a virtual python environment
python -m venv .
source bin/activate;

# Install black to format python code when developing
python -m pip install black;

# Build the dist files for local development
nvm use;
npm install;

# Checkout any git submodules in this repo if didn't
# `git clone --recurse-submodules ...`.
git submodule init;
git submodule update;

# If using site-specific-content then create symbolic links to that content from
# that git submodule. A Makefile should be in the site-specific-content
directory.
(if [ -d site-specific-content ]; then
  cd site-specific-content
  make
  make install
fi)

# Build the dist files for local development
npm run build;

# Upload the changes to the development machine
./bin/devsync.sh
```

The limits for ImageMagick may need to be updated. Copy the
`/etc/ImageMagick-6/policy.xml` file from your development machine and replace
the one included with the project. Check the differences and either edit it or
use what the project has set. _This step is optional_, but the policy file will
still be updated when running the `make install` command. When the
`make uninstall` is used it is restored to how it was before.

```bash
# Grab the policy from your development machine.
scp dev@local-puzzle-massive:/etc/ImageMagick-6/policy.xml resources/imagemagick-policy.xml;

# Show the differences.
git diff resources/imagemagick-policy.xml;

# Use what was set for the project if it looked okay.
git checkout resources/imagemagick-policy.xml;
```

### Initialize the development machine

Should be logged into the development machine.

```bash
ssh dev@local-puzzle-massive;
```

```bash
cd /usr/local/src/puzzle-massive/;

# Setup to use a virtual python environment
python -m venv .
source bin/activate;

# Makes the initial development version
make;

# Install the files that were compiled.
sudo make install;

# Stop the apps here since we need to update the database.
sudo ./bin/appctl.sh stop -f;

# Create the puzzle database tables and initial data
python api/api/create_database.py site.cfg;

# Update any bit icon authors and add new bit icons if applicable
python api/api/jobs/insert-or-replace-bit-icons.py

# Update the enabled puzzle features if applicable
python api/api/update_enabled_puzzle_features.py

# Test and reload the nginx configurations
sudo nginx -t;
sudo systemctl reload nginx;

# Start the apps and monitor the logs
sudo ./bin/appctl.sh start;
sudo ./bin/log.sh;
```

## Developing Puzzle Massive locally and creating puzzles

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

Should be logged into the development machine.

```bash
ssh dev@local-puzzle-massive;
```

```bash
cd /usr/local/src/puzzle-massive/;
source bin/activate;

puzzle-massive-testdata players --count=100;

puzzle-massive-testdata puzzles --count=30 --min-pieces=9 --pieces=200 --size=180x180\!;
puzzle-massive-testdata puzzles --count=10 --min-pieces=20 --pieces=900 --size=800x1500\!;
puzzle-massive-testdata puzzles --count=10 --min-pieces=20 --pieces=900 --size=1800x1300\!;
puzzle-massive-testdata instances --count=10 --min-pieces=20 --pieces=500;
puzzle-massive-testdata puzzles --count=1 --pieces=2000 --size=3800x3500\!;
```

<!-- TODO: Add a visual of how the different apps are currently set up. Should
show the current limitations of the sqlite database and any apps that use it
(have read access) are required to be on the same server. -->

### Python Unit Tests

Some unit tests exist to cover parts of the api application. Some older tests
have been skipped since they were not actively maintained. The existing ones can
be run with the following commands.

Should be logged into the development machine.

```bash
ssh dev@local-puzzle-massive;
```

```bash
cd /usr/local/src/puzzle-massive/;
source bin/activate;

# Run all the tests for the api
python -m unittest discover --start-directory api --failfast

# Run specific tests
python api/api/test_puzzle_details.py

# Run specific test case
python api/api/test_puzzle_details.py TestInternalPuzzleDetailsView.test_missing_payload
```

### Building the `dist/` files

The javascript and CSS files in the `dist/` directory are built from the source
files in `src/` by running the `npm run build` command from your local machine. This uses
[rollup](http://rollupjs.org/) and is configured with the
`rollup.config.js`. The entry file is `src/index.js` and following that the
main app bundle (`app.bundle.js`, `app.bundle.css`) is built from
`src/app.js`.

The source files for javascript and CSS are organized mostly as components. The
`src/site/` being an exception as it includes CSS and javascript used across the
whole site. Each component includes its own CSS (if applicable) and the CSS
classes follow the
[SUIT CSS naming conventions](https://github.com/suitcss/suit/blob/master/doc/naming-conventions.md).

When editing files in `src/` either run `npm run debug` or `npm run watch`. The
production version is done with `npm run build` which will create compressed
versions of the files. To upload the just compiled files in the `dist/`
directory use the `bin/devsync.sh` command.

```bash
# Build the dist files and rsync them to the development machine
npm run debug && ./bin/devsync.sh;

# Or watch for changes in src/, build, and rsync to development machine
./bin/distwatch.js &
npm run watch;
pkill --full -u $(whoami) "\./bin/distwatch\.js";
```

## Creating a versioned dist for deployment

After making any changes to the source files; commit those changes to git in
order for them to be included in the distribution file. The distribution file
is uploaded to the server and the guide to do deployments should then be
followed.

To create the versioned distribution file (like `puzzle-massive-2.0.0.tar.gz`) use the
`make dist` command from your local machine. Note that the version is set in the `package.json`.

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

### Site specific chill data

The site specific pages and other nav menu links no longer live in the Puzzle
Massive source code. This allows for other custom sites to use puzzle-massive
code, but include pages that are specific for that distribution. The
`chill-data` directory is where these custom sites can include any site specific
chill data yaml files. These chill data yaml files can also reference other
templates, documents, and queries by adding files in the respective 'other'
directory.

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
git clean -dx -e /.env -e /.has-certs -e /web -n

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
git clean -fdx --exclude=.env;
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

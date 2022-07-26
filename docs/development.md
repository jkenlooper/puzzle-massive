# Local Development Guide

Get a **local development** version of Puzzle Massive to run on your machine by
following this guide. You'll need to install the below software in order to
create a virtual machine and create containers.

- [VirtualBox](https://www.virtualbox.org/)
- [Vagrant](https://www.vagrantup.com/)
- [Docker](https://www.docker.com/) or [Podman](https://podman.io/)

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
  http://localhost:38682/ .
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
your local machine. [Docker](https://www.docker.com/) or equivalent container runtime like [Podman](https://podman.io/) will also be needed. This allows you to run your own version of Puzzle Massive
locally. The [Vagrantfile](../Vagrantfile) included with the project is for
local development only. It has a few scripts within it that help setup a local
version of Puzzle Massive. This can all be set up by running the below
`vagrant` commands.

```bash
# Compile the client-side theme files
cd client-side-public && make && cd -

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
vagrant provision --provision-with shell-init-dev-local
```

### Add Random Puzzles

At this point the site at http://localhost:38682/ should be working on your local
machine. It won't have any puzzles or any players initially. To add some
random puzzles to work with and test things run these optional vagrant
provisioning scripts.

These will create some random images and then upload them much like how the
puzzle upload form works. If the site wasn't configured to automatically
approve any submitted puzzles (see AUTO_APPROVE_PUZZLES in the `.env` file),
then you'll need to manually approve these. Go to the admin page to view any
puzzles that have been submitted for approval
http://localhost:38682/chill/site/admin/puzzle/submitted/

```bash
# Optional if needing a few initial puzzles to work with.
vagrant provision --provision-with shell-testdata-puzzles-quick

# Optional if needing lots of puzzles to work with. This may take a few minutes.
vagrant provision --provision-with shell-testdata-puzzles
```

### Edit the Source Code

This project has both server-side code written in mostly Python as well as
client-side code that a web browser uses. All the client-side Javascript, HTML,
and CSS is located in the `client-side-public/src/` directory. After making changes to these files
it will be necessary to copy them over to the virtual machine. This can either
be done with the `vagrant rsync` command to do it once, or you can open another
terminal window and have it always update whenever a change to a file is made
with the `vagrant rsync-auto` command.

```bash
# Compile the client-side theme files
cd client-side-public && make && cd -

# Copy the files to the virtual machine.
vagrant rsync legacy_puzzle_massive
```

```bash
# Or continually watch files for any changes and copy them to the virtual
# machine.
vagrant rsync-auto legacy_puzzle_massive
```

### Troubleshoot Errors on the Vagrant Virtual Machine

Errors from running the app are accessible if you ssh into the development
machine. Vagrant has a command for this which is `vagrant ssh`. After logging in
you'll see the `puzzle-massive/` directory at `/home/vagrant/`. This is where
all the files from your project directory are uploaded to. However, this is
**not** the actual files that are used for the running development machine. The
actual files that are being used for the site are in the
`/usr/local/src/puzzle-massive/` directory and are owned by the 'dev' user. Any
file changes in `/home/vagrant/puzzle-massive/` will be automatically copied
over to `/usr/local/src/puzzle-massive/` via the
`local-puzzle-massive-auto-devsync` service.

```bash
# Log into the Vagrant development machine
vagrant ssh
```

Note that after logging into the development machine as the vagrant user; that
there is a 'dev' user. The 'dev' user owns the `/user/local/src/puzzle-massive/`
directory and in order to start and stop the services, or manipulate the
database, you'll need to login as that user.

```bash
# Switch to the dev user
sudo su dev
```

#### Errors with Compiling `client-side-public/src/` Files

See [client-side-public/README.md](../client-side-public/README.md)

#### Errors with Python Code

...WIP

#### Errors with Template Code Used in HTML Pages

...WIP

### Maintenance Tasks

#### Update packages and reboot

```bash
# Requires ansible to be installed.
vagrant provision --provision-with update-packages-and-reboot
```

#### Test out in-place deployment

Normally there is no need to do a in-place quick deploy on the virtual machine
since it is usually in development mode and will build as needed. The below
Ansible playbook can be used to test out the created dist file on the virtual
machine. Create the dist file with the `make dist` command on the local machine.

```bash
# Replace 'puzzle-massive-2.x.tar.gz' with actual dist file that was created.
DIST_FILE=../../puzzle-massive-2.x.tar.gz \
vagrant provision --provision-with in-place-quick-deploy
```

#### Restore data

Sync a local resources directory to the development machine. Defaults to
`_infra/local/output/resources` if not defining the environment variable
RESOURCES_DIRECTORY.

```bash
vagrant provision --provision-with sync-legacy-puzzle-massive-resources-directory-from-local
```

A db.dump.gz file can also replace an existing database on the development
machine. This will default to `_infra/local/output/db.dump.gz` if not defining
the environment variable DB_DUMP_FILE.

```bash
vagrant provision --provision-with restore-db-on-legacy-puzzle-massive
```

Note that there is a trigger set for 'vagrant halt' and 'vagrant destroy'
commands that will create a `_infra/local/output/db.dump.gz` file of the
existing database. It also synchronizes the `_infra/local/output/resources`
directory. The resources directory could be empty if the site is not configured
to use local resources.

The fake s3 server running in the virtual machine will automatically save it's
data to the `_infra/local/output/s3rver` directory when the 'vagrant up' command
is used.

### Python Unit Tests

Some unit tests exist to cover parts of the application. Some older tests
have been skipped since they were not actively maintained. The existing ones can
be run with the following commands.

Should be logged into the development machine.

```bash
vagrant ssh
```

```bash
sudo su dev
cd /usr/local/src/puzzle-massive/;
source bin/activate;

# Run all the tests for the api
python -m unittest discover --start-directory api --failfast

# Run specific tests
python api/api/test_puzzle_details.py

# Run specific test case
python api/api/test_puzzle_details.py TestInternalPuzzleDetailsView.test_missing_payload
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

# Quick Start Guide

Follow this guide instead of the [local development guide](development.md) to
get a working version of Puzzle Massive available locally on your own machine.
After following the steps listed here; the local development version of Puzzle
Massive will be running on http://localhost:8080/ and will have a few
pre-generated puzzles and some mock player data in order to show the different
user interfaces.  This also doesn't require extensive knowledge with the command
line and managing services on the virtual machine with ssh.

Install [VirtualBox](https://www.virtualbox.org/) and
[Vagrant](https://www.vagrantup.com/) on your system.  These two applications
allow creating a virtual machine on your Mac or Windows operating system.

Create an account on [GitHub](https://github.com/) if you don't already have
one.  Set up Git on your machine and install the GitHub Desktop client by
following the 
[GitHub set up guide](https://help.github.com/en/articles/set-up-git).

Then fork the [puzzle-massive](https://github.com/jkenlooper/puzzle-massive)
repository.  That way your changes to the source code will be under version
control.  This makes contributing improvements to the code easier and getting
future updates from new versions.

After cloning your own fork of the puzzle-massive repo; open a terminal and `cd`
to that directory.  All the commands after this assume that the current working
directory is the top level of the puzzle-massive project (the directory that has
the `package.json` file in it).

The virtual machine can be provisioned and started up.  Use the command
`vagrant up` to accomplish this.  It will download the pre-built Vagrant box
[jkenlooper/puzzle-massive](https://app.vagrantup.com/jkenlooper/boxes/puzzle-massive).
The virtual machine uses a shared folder with the host machine.  This shared
folder is located at `/vagrant/` on the virtual machine and is the same folder
that the `Vagrantfile` is in.

The source files in the `/vagrant/` shared directory have not been compiled and
built yet.  Open a terminal with the working directory set to the same file the
`Vagrantfile` is in and do the following commands to start.

```bash
# Provision and start up the virtual machine
vagrant up;

# SSH in to the virtual machine
vagrant ssh;

# Change to the shared /vagrant directory
cd /vagrant/;

# Copy over the included .env and .htpasswd files to the shared /vagrant
# Skip doing this if you already have these files.
cp ~/.env ~/.htpasswd /vagrant/;

# Build and install

# Isolate the python environment and make it active
virtualenv .;
source bin/activate;

# Use nvm to set Node version 
nvm use;

# Install front end build tools and dependencies
npm install;

# Build all the front end code in src/
npm run build;

# Build the apps for the site and create the configuration files
make;

# Install the apps
sudo make install;

# Start the site and reload the web server config
sudo ./bin/puzzlectl.sh start
sudo systemctl reload nginx;

# Log out of the virtual machine
exit;
```

The pre-built box will already have some puzzles generated and the steps to do
the initial set up are done.  The local version will run on your host machine at
[http://localhost:8080/](http://localhost:8080/) .  The services are all running
in debug or development mode so are not optimized for handling production
traffic.  The response time may slow down after a while because of this.
A simple restart of the virtual machine will be needed periodically.

To stop the site run the `puzzlectl.sh stop` command.

```bash
# Stop the site
vagrant ssh --command "sudo /vagrant/bin/puzzlectl.sh stop"

# Shutdown the virtual machine
vagrant halt
```

To start the site again run these commands.

```bash
# Start the virtual machine
vagrant up;

# Start the site
vagrant ssh --command "sudo /vagrant/bin/puzzlectl.sh start"
```

The `puzzlectl.sh` script is used to manage the different services running for
the site.  Other sub commands besides `stop` can be used such as `start`, and
`status`.

The `bin/log.sh` is used to show the logging for the puzzle apps that are
running.  It is sometimes useful to monitor that when troubleshooting.

```bash
vagrant ssh --command "/vagrant/bin/log.sh"
```

## Making changes to code in `src/`

The source code in the `src/` directory is all Javascript, HTML, and CSS.  The
files in `dist/` are compiled from the files in `src/`.  The site is configured
to serve files in `dist/` folder under the URL
http://localhost:8080/theme/2.2.0/ where '2.2.0' is the current version in
`package.json`.  So, in order for any changes to files in `src/` to be shown on
the site, a command to compile or build those `dist/` files need to happen.  The
`npm` command is used to accomplish this and will run various scripts needed.
Note that `npm` command is only used from the virtual machine and **not** from
your host machine.  This one liner below uses `ssh` to first login to the
virtual machine before running `npm`.

```bash
# Run this command if files in src/ have changed.
vagrant ssh --command "cd /vagrant/; ./bin/npmrun.sh build" 
```

When editing files in `src/` and debugging things use the `debug` instead of
`build`.  This will create `dist/` files that are not compressed.

```bash
# Run this command if files in src/ have changed and needing to debug.
vagrant ssh --command "cd /vagrant/; ./bin/npmrun.sh debug" 
```

## List of puzzle images that were included

The puzzles listed below are included with the pre-built vagrant box.  Some
images used are the lower resolution variant to get a smaller puzzle piece
count.  This is mostly done to easily test completing a puzzle and such.

pieces | actual | background | link
------ | ------ | ---------- | ----
200 | 80 | #224D80 | https://en.wikipedia.org/wiki/File:SantaCruz-CuevaManos-P2210651b.jpg
2500 | 2288 | #ADDEB1 | https://en.wikipedia.org/wiki/File:Ruby_Loftus_screwing_a_Breech-ring_(1943)_(Art._IWM_LD_2850).jpg
200 | 15 | #224D80 | https://en.wikipedia.org/wiki/File:Nighthawks_by_Edward_Hopper_1942.jpg
300 | 300 | #261A26 | https://en.wikipedia.org/wiki/File:Irises-Vincent_van_Gogh.jpg
1200 | 1178 | #16161F | https://en.wikipedia.org/wiki/File:Vincent_van_Gogh_-_Wheat_Field_with_Cypresses_(National_Gallery_version).jpg
800 | 792 | #BA9393 | https://en.wikipedia.org/wiki/File:Albert_Bierstadt_-_The_Rocky_Mountains,_Lander%27s_Peak.jpg
350 | 320 | #CECFAB | https://en.wikipedia.org/wiki/File:Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg
200 | 12 | #C2919D | https://en.wikipedia.org/wiki/File:Meisje_met_de_parel.jpg
2000 | 1989 | #224D80 | https://en.wikipedia.org/wiki/File:%22The_School_of_Athens%22_by_Raffaello_Sanzio_da_Urbino.jpg

### Admin view for managing puzzles

The admin view of the site is by default protected with basic auth and requires
editing the included `.htpasswd` file if needing a different or more secure
user/pass.  The pre-built vagrant box which should **only** be used for
development purposes has the 'admin' user set with 'admin' as password.  Visit
http://localhost:8080/chill/site/admin/puzzle/ to manage the puzzles on the
site.

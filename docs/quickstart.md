# Quick Start Guide

_Work in Progress_ and is not tested yet.

Follow this guide instead of the [Local Development Guide](development.md) to
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

The `Vagrantfile` in the project is set to a base box for Ubuntu.  For the quick
start setup it will use the pre-built Vagrant box.  Use `vagrant init -f` to
overwrite the `Vagrantfile` with this pre-built Vagrant box.

```bash
# Create new Vagrantfile replacing the current one
vagrant init -f jkenlooper/puzzle-massive
```

Now the virtual machine can be provisioned and started up.  Use the command
`vagrant up` to accomplish this.

```bash
vagrant up;

# TODO: add the .env, .htpasswd, and dist that were packaged

# Run some initial setup
vagrant ssh;
cd /vagrant/;
virtualenv .;
source bin/activate;
nvm use;
npm install;
npm run build;
make;
sudo make install;
```

The pre-built box will already have some puzzles generated and the steps to do
the initial set up are done.  The local version will run on your host machine at
[http://localhost:8080/](http://localhost:8080/) .  The services are all running
in debug or development mode so are not optimized for handling production
traffic.  The response time may slow down after a while because of this.
A simple restart of the virtual machine will be needed periodically.

To start the site run the `puzzlectl.sh start` command.

```bash
vagrant ssh --command "sudo /vagrant/bin/puzzlectl.sh start"
```

The `puzzlectl.sh` script is used to manage the different services running for
the site.  Other sub commands besides `start` can be used such as `stop`, and
`status`.

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
`build`.  This will create `dist/` files that are not compressed.  Use the
`watch` sub command to automatically compile the files with each change in
`src/` directory.

```bash
# Run this command if files in src/ have changed and needing to debug.
vagrant ssh --command "cd /vagrant/; ./bin/npmrun.sh debug" 

# Run this command to automatically compile src/ files when they are changed.
# TODO: the watched files don't seem to work when shared from the /vagrant/ directory
vagrant ssh --command "cd /vagrant/; ./bin/npmrun.sh watch" 
# Use 'ctrl c' to stop the command
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

----

... Work in Progress ...

TODO: publish the jkenlooper/puzzle-massive box

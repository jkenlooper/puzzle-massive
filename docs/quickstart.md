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
vagrant up
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

----

... Work in Progress ...

TODO: publish the jkenlooper/puzzle-massive box

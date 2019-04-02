# Quick Start Guide

_Work in Progress_ and is not tested yet.

Follow this guide instead of the [Local Development Guide](development.md) when
**only** modifying the `src/` files.  This uses a pre-built Vagrant box that is
setup to automatically build the files in the `dist/` directory when the source
files in `src/` change.  This also doesn't require extensive knowledge with the
command line and managing services on the virtual machine with ssh.

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
traffic.  The response time may slow down may slow down after a while because of this.  A simple restart of the virtual machine will sometimes be needed.


----

... Work in Progress ...

TODO: publish the jkenlooper/puzzle-massive box
TODO: Auto set the npm run build when files change in src/
TODO: Serve on localhost if not already.

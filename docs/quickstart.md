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

## List of puzzle images that were included

At this time the initial puzzles included with the pre-built vagrant box are
added manually when creating it.  The list below shows the necessary data to
recreate it.  In the future this process might be automated with a script.
Maybe it could use cypress or some other end to end testing framework.

pieces | background | link | description
------ | ---------- | ---- | -----------
20 | #224D80 | https://en.wikipedia.org/wiki/File:SantaCruz-CuevaManos-P2210651b.jpg | Hands at the Cuevas de las Manos upon Río Pinturas, near the town of Perito Moreno in Santa Cruz Province, Argentina. Picture taken by me in 2005.
500 | #224D80 | https://en.wikipedia.org/wiki/File:Ruby_Loftus_screwing_a_Breech-ring_(1943)_(Art._IWM_LD_2850).jpg | A young factory worker in blue overalls is shown at work on a industrial lathe, cutting and turning the breech-ring component of a Bofors anti-aircraft gun. Other factory workers are visible in the background.
200 | #224D80 | https://en.wikipedia.org/wiki/File:Nighthawks_by_Edward_Hopper_1942.jpg | Nighthawks, Edward Hopper
300 | #224D80 | https://en.wikipedia.org/wiki/File:Irises-Vincent_van_Gogh.jpg | Irises, Vincent van Gogh
1200 | #224D80 | https://en.wikipedia.org/wiki/File:Vincent_van_Gogh_-_Wheat_Field_with_Cypresses_(National_Gallery_version).jpg | Wheat Field with Cypresses, Vincent van Gogh
800 | #224D80 | https://en.wikipedia.org/wiki/File:Albert_Bierstadt_-_The_Rocky_Mountains,_Lander%27s_Peak.jpg | Albert Bierstadt - The Rocky Mountains, Lander's Peak
4000 | #224D80 | https://en.wikipedia.org/wiki/File:Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg | Van Gogh - Starry Night
30 | #224D80 | https://en.wikipedia.org/wiki/File:Meisje_met_de_parel.jpg | Girl with a Pearl Earring, Johannes Vermeer
2000 | #224D80 | https://en.wikipedia.org/wiki/File:%22The_School_of_Athens%22_by_Raffaello_Sanzio_da_Urbino.jpg | Raphael - The School of Athens


----

... Work in Progress ...

TODO: publish the jkenlooper/puzzle-massive box

TODO: add puzzles automatically?

# Puzzle Massive

A Massively Multiplayer Online Jigsaw Puzzle as a web application.  Jigsaw
puzzles are made from randomly generated classic interlocking pieces and can be
5000+ pieces.  Players can collaborate on the same jigsaw puzzle in real time.
Other player's piece movements are moderated automatically in order to prevent
abusive behavior.

**A live version is hosted at [puzzle.massive.xyz](http://puzzle.massive.xyz).**

Bugs and feature requests can be tracked via the projects source code repository
https://github.com/jkenlooper/puzzle-massive/issues
or send an email to puzzle-bug@massive.xyz with a description.

This project has been moved to GitHub with a fresher git commit history. The
previous git commit history is available upon request.  I've chosen to make
Puzzle Massive an open source project under the GNU Affero General Public
License.

[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com) 

[![Chat on Discord](https://img.shields.io/badge/chat-on%20Discord-green.svg)](https://discord.gg/uVhE2Kd)

## Get started

Get a local development version of Puzzle Massive to run on your machine by
following these instructions.

The deployment and structure has been generated from this
[cookiecutter](https://github.com/jkenlooper/cookiecutter-website).

Written for a Linux machine that is Debian based.  Only tested on Ubuntu.  Use
 [VirtualBox](https://www.virtualbox.org/) and
 [Vagrant](https://www.vagrantup.com/) or something similar if not on a Linux
 machine.

If using Vagrant; then run `vagrant up` and ssh in (`vagrant ssh`) and go to
the /vagrant/ shared directory when running the rest of the commands.

Run the `bin/init.sh` script to configure the server with ssh and a user if
needed. Don't need to run this if using Vagrant.

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
```
sudo passwd dev;
su dev;
```

Create the `.env` and `.htpasswd` files first. 
```
echo "UNSPLASH_APPLICATION_ID=fill-this-in" > .env;
echo "UNSPLASH_APPLICATION_NAME=fill-this-in" >> .env;
echo "UNSPLASH_SECRET=secret-key-goes-here" >> .env;
echo "NEW_PUZZLE_CONTRIB=temporary-contributor-id-goes-here" >> .env;
echo "SUGGEST_IMAGE_LINK='https://any-website-for-uploading/'" >> .env;
echo "SECURE_COOKIE_SECRET=make-up-some-random-text" >> .env;
echo "SMTP_HOST='localhost'" >> .env;
echo "SMTP_PORT='587'" >> .env;
echo "SMTP_USER='user@localhost'" >> .env;
echo "SMTP_PASSWORD='somepassword'" >> .env;
echo "EMAIL_SENDER='sender@localhost'" >> .env;
echo "EMAIL_MODERATOR='moderator@localhost'" >> .env;
htpasswd -c .htpasswd admin;
```


When first installing on the dev machine run:

```
virtualenv .;
source bin/activate;
make;
cp chill-data.sql db.dump.sql;
npm install;
npm run build;
sudo make install;

# As the dev user:
sudo su dev
source bin/activate
python api/api/create_database.py site.cfg;
exit

sudo nginx -s reload
```

Set the credentials to use a compatible s3 setup with either the awscli or
manually adding the credentials.
```
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

## Getting Help

I try to monitor the chat channels on the [Discord server for Puzzle
Massive](https://discord.gg/uVhE2Kd).  This project is slightly complex with
a few moving pieces (pun intended); that being said, there is a good chance that
a piece or two are missing when putting the project together.  If you have ran
into a problem getting this project working on your own machine; please ask for
help.  I'm looking to improve the process where I can and am looking for more
experience helping others in web development stuff like this.


## License

Puzzle Massive. An online multiplayer jigsaw puzzle.
Copyright (C) 2018 Jake Hickenlooper

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.


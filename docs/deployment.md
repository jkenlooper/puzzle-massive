# Deployment Guide

There are two kinds of deployments outlined here.  The first one is for in-place
deployments where only minor changes are needed and don't require any services
to be restarted.  These are usually updates to the client-side resources like
Javascript, CSS, and HTML or other graphic files. The other type of deployment
is commonly called a blue-green deployment where a new server is created and
then when everything has been deployed and ready; traffic is directed to the new
server.

## Create a new version for the deployment

Deployments should use a versioned distribution file that is uploaded to the
server.  This file can be made after a new version has been created with `npm
version`.  On the development machine build the versioned distribution file.

```
make dist;
```

The distribution file will be at the top level of the project and named after
the version found in package.json.  For example, with version 2.0.0 the file is
`puzzle-massive-2.0.0.tar.gz`.

That tar file can then be uploaded to the server.  The next step varies
depending if the deployment will be an in-place deployment or if a new server
is being created.


## In-place Deployments

The client-side resources should first be made for production and not
development.  Then use the yet to be created bin/sync.sh script to upload those
changed files to the running server.

### Steps

TODO: Steps when doing in-place deployments.

## Blue-Green Deployments

Create a new server and transfer data over from the old one.

### Steps

After the tar file has been uploaded to the server; SSH in and expand it to the
`/usr/local/src/` directory.

```
tar --directory=/usr/local/src/ --extract --gunzip -f puzzle-massive-2.0.0.tar.gz
```

Now setup the new server by running the init and setup scripts.  These should be
run with root privileges (prepend these commands with 'sudo' if not root user).

```
cd /usr/local/src/puzzle-massive/;
./bin/init.sh;
./bin/setup.sh;
```

Log in as the dev user and upload or create the `.env` and `.htpasswd` files in
the `/usr/local/src/puzzle-massive/` directory (See README).

Now create the initial bare-bones version without any data as the dev user.

```
virtualenv .;
source bin/activate;
make ENVIRONMENT=production;
cp chill-data.sql db.dump.sql;
sudo make ENVIRONMENT=production install;

# should be run as 'dev' user
python api/api/create_database.py site.cfg;
```

The logs for all the apps for Puzzle Massive can be followed with the
`./bin/log.sh` command.  It is just a shortcut to doing the same with
`journalctrl`.

Check the status of the apps with this convenience command to `systemctl`.
```
sudo ./bin/puzzlectl.sh status;
```

Test and reload the nginx config.

```
sudo nginx -t &&
sudo nginx -s reload
```

Note that by default the production version of the nginx conf for Puzzle Massive
is hosted at http://puzzle.massive.xyz/ as well as http://puzzle-blue/ and
http://puzzle-green/ .  You can edit your `/etc/hosts` to point to the old
(puzzle-blue) and new (puzzle-green) servers.

### Transferring data from the old server to the new server

At this point two servers should be running Puzzle Massive with only the older
one having traffic.  The new one should be verified that everything is working
correctly by doing some integration testing.  The next step is to stop the apps
on the old server and copy all the data over to the new puzzle-green server.

On the old server; stop the apps and migrate the data out of redis. Otherwise,
leave the old server untouched in case something fails on the new server.

```
sudo ./bin/puzzlectl.sh stop;
./bin/backup-db.sh;
```

On the new server the files from the old server will be copied over with rsync.
First step here is to stop the apps on the new server and remove the initial db
and any generated test puzzles.

```
sudo ./bin/puzzlectl.sh stop;
```

Copy the backup db (db-YYYY-MM-DD.dump.gz) to the new server and replace the
other one (SQLITE_DATABASE_URI).

```
DBDUMPFILE="db-$(date +%F).dump.gz";
rsync --archive --progress --itemize-changes \
  dev@puzzle-blue:/usr/local/src/puzzle-massive/$DBDUMPFILE \
  /usr/local/src/puzzle-massive/;
mv /var/lib/puzzle-massive/sqlite3/db db.backup;
zcat $DBDUMPFILE | sqlite3 /var/lib/puzzle-massive/sqlite3/db
```

Copy the nginx logs (NGINXLOGDIR) found at: `/var/log/nginx/puzzle-massive/`

```
rsync --archive --progress --itemize-changes \
  dev@puzzle-blue:/var/log/nginx/puzzle-massive \
  /var/log/nginx/puzzle-massive
```

Copy the archive directory (ARCHIVEDIR): `/var/lib/puzzle-massive/archive/`

```
rsync --archive --progress --itemize-changes \
  dev@puzzle-blue:/var/lib/puzzle-massive/archive \
  /var/lib/puzzle-massive/archive
```

Copy the resources directory (SRVDIR/resources) that contains the generated puzzles:

```
rsync --archive --progress --itemize-changes \
  dev@puzzle-blue:/srv/puzzle-massive/resources \
  /srv/puzzle-massive/resources
```

### Start the new server

After the old server data has been copied over, then start up the new server
apps with the 'puzzlectl.sh' script.  It is also good to monitor the logs to see
if anything is throwing errors.

```
sudo ./bin/puzzlectl.sh start;
./bin/log.sh;
```

Verify that the new version of Puzzle Massive is running correctly on
puzzle-green/. If everything checks out, then switch the traffic over to
puzzle.massive.xyz/. 

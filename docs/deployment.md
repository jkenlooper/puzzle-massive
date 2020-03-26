# Deployment Guide

There are two kinds of deployments outlined here. The first one is for in-place
deployments where only minor changes are needed and don't require any services
to be restarted. These are usually updates to the client-side resources like
Javascript, CSS, and HTML or other graphic files. The other type of deployment
is commonly called a blue-green deployment where a new server is created and
then when everything has been deployed and ready; traffic is directed to the new
server.

## Create a new version for the deployment

Deployments should use a versioned distribution file that is uploaded to the
server. This file can be made after a new version has been created with `npm version`. On the **development machine** build the versioned distribution file.
Please follow these _super awesome instructions_ in the [Local development
guide](development.md) in order to build a dist file.

```bash
make dist;
```

The distribution file will be at the top level of the project and named after
the version found in package.json. For example, with version 2.0.0 the file is
`puzzle-massive-2.0.0.tar.gz`.

That tar file can then be uploaded to the server. The next step varies
depending if the deployment will be an in-place deployment or if a new server
is being created.

## In-place Deployments

Normally the choice to do an in-place deployment instead of a blue-green
deployment is that the change is very minimal and it would just be faster.
These changes are usually simple updates to the client-side resources or minor
patches to the running apps.

SSH into the server as the 'dev' user after the versioned distribution file has
been uploaded to the home directory.

### Steps

1.  Stop the running apps and backup the db. The deactivate command is done to
    deactivate the python virtualenv. A backup of the database is made just as
    a cautionary measure and is left in the folder. The backup-db.sh script
    also moves data out of redis and into the database.

    ```bash
    cd /usr/local/src/puzzle-massive;
    source bin/activate;
    printf 'Updating...' > /srv/puzzle-massive/root/puzzle-massive-message.html;
    sudo ./bin/puzzlectl.sh stop;
    sudo ./bin/clear_nginx_cache.sh;
    ./bin/backup-db.sh -c;
    deactivate;
    ```

2.  Replace the current source code with the new version. Example shows the
    puzzle-massive-2.0.0.tar.gz which should be in the dev home directory. The
    current source code is moved to the home directory under a date label in
    case it needs to revert back. The `.env` and `.htpasswd` files are copied
    over since they are not included in the distribution.

    ```bash
    PM_DATE="$(date --iso-8601 --utc)";
    cd /home/dev/;
    sudo mv /usr/local/src/puzzle-massive "puzzle-massive-${PM_DATE}";
    sudo tar --directory=/usr/local/src/ --extract --gunzip -f puzzle-massive-2.0.0.tar.gz
    sudo chown -R dev:dev /usr/local/src/puzzle-massive
    cp "puzzle-massive-${PM_DATE}/.env" /usr/local/src/puzzle-massive/;
    cp "puzzle-massive-${PM_DATE}/.htpasswd" /usr/local/src/puzzle-massive/;
    ```

3.  Make the new apps and install the source code. The install will also start
    everything back up. The last command to test and reload nginx is optional
    and is only needed if the nginx conf changed.

    ```bash
    cd /usr/local/src/puzzle-massive;
    virtualenv . -p python3;
    source bin/activate;
    make ENVIRONMENT=production && \
    sudo make ENVIRONMENT=production install;
    sudo nginx -t && \
    sudo systemctl reload nginx;
    printf '' > /srv/puzzle-massive/root/puzzle-massive-message.html;
    sudo ./bin/clear_nginx_cache.sh;
    ```

4.  Verify that stuff is working by monitoring the logs.

    ```bash
    sudo ./bin/puzzlectl.sh status;
    sudo ./bin/log.sh;
    ```

## Blue-Green Deployments

Create a new server and transfer data over from the old one. This is a good
choice of deployment when the changes are more significant and would benefit
from being able to test things a bit more thoroughly before having it accessible
by the public.

### Steps

1.  After the tar file has been uploaded to the server; SSH in and expand it to
    the `/usr/local/src/` directory. This is assuming that only root can SSH in
    to the server and the distribution was uploaded to the /root/ directory.

    ```bash
    cd /root;
    tar --directory=/usr/local/src/ --extract --gunzip -f puzzle-massive-2.0.0.tar.gz
    ```

2.  Now setup the new server by running the `init.sh` and `setup.sh` scripts.
    These should be run with root privileges (prepend these commands with 'sudo'
    if not root user). The init.sh script will ask for the id_rsa.pub key which
    can just be pasted in. The ownership of the source code files are switched
    to dev since it was initially added via root user.

    ```bash
    cd /usr/local/src/puzzle-massive/;
    ./bin/init.sh;
    ./bin/setup.sh;
    chown -R dev:dev /usr/local/src/puzzle-massive
    ```

3.  SSH in as the dev user and upload or create the `.env` and `.htpasswd` files
    in the `/usr/local/src/puzzle-massive/` directory. See the README on how to
    create these. At this point there is no need to SSH in to the server as the
    root user.

4.  Now create the initial bare-bones version without any data as the dev user.

    ```bash
    cd /usr/local/src/puzzle-massive/;
    virtualenv . -p python3;
    source bin/activate;
    make ENVIRONMENT=production;
    sudo make ENVIRONMENT=production install;
    sudo ./bin/puzzlectl.sh stop;

    # Update the limits in /etc/ImageMagick-6/policy.xml
    # Refer to notes in api/api/jobs/pieceRenderer.py

    # should be run as 'dev' user
    python api/api/create_database.py site.cfg;

    sudo ./bin/puzzlectl.sh start;
    ```

5)  The logs for all the apps for Puzzle Massive can be followed with the
    `./bin/log.sh` command. It is just a shortcut to doing the same with
    `journalctrl`.

    Check the status of the apps with this convenience command to `systemctl`.

    ```bash
    sudo ./bin/puzzlectl.sh status;
    ```

6)  Test and reload the nginx config.

    ```bash
    sudo nginx -t && \
    sudo systemctl reload nginx
    ```

7.  _This step is not necessary. The site isn't using https yet._

    Set up the production server with TLS certs. [certbot](https://certbot.eff.org/)
    is used to deploy [Let's Encrypt](https://letsencrypt.org/) certificates.
    This will initially fail if the server isn't accepting traffic at the domain
    name. The certs can be copied over from the live server later.

    ```bash
    cd /usr/local/src/puzzle-massive/;
    source bin/activate;
    sudo bin/provision-certbot.sh /srv/puzzle-massive/
    make ENVIRONMENT=production;
    sudo make ENVIRONMENT=production install;
    sudo nginx -t && \
    sudo systemctl reload nginx
    ```

8.  Generate some random data and test.

    ```bash
    puzzle-massive-testdata players --count=100;

    puzzle-massive-testdata puzzles --count=2 --min-pieces=200 --pieces=900 --size=1800x1300\!;
    puzzle-massive-testdata puzzles --count=2 --min-pieces=200 --pieces=900 --size=800x1500\!;
    puzzle-massive-testdata puzzles --count=1 --pieces=2000 --size=3800x3500\!;
    puzzle-massive-testdata puzzles --count=300 --pieces=9 --size=180x180\!;

    puzzle-massive-testdata instances --count=10 --min-pieces=9 --pieces=50;
    ```

Note that by default the production version of the nginx conf for Puzzle Massive
is hosted at http://puzzle.massive.xyz/ as well as http://puzzle-blue/ and
http://puzzle-green/ . You can edit your `/etc/hosts` to point to the old
(puzzle-blue) and new (puzzle-green) servers.

### Transferring data from the old server to the new server

At this point two servers should be running Puzzle Massive with only the older
one having traffic. The new one should be verified that everything is working
correctly by doing some integration testing. The next step is to stop the apps
on the old server and copy all the data over to the new puzzle-green server.

1.  On the **old server** stop the apps and migrate the data out of redis. The old
    server is left untouched in case something fails on the new server.

    ```bash
    cd /usr/local/src/puzzle-massive/;
    source bin/activate;
    printf 'Updating...' > /srv/puzzle-massive/root/puzzle-massive-message.html;
    sudo ./bin/puzzlectl.sh stop;
    sudo ./bin/clear_nginx_cache.sh;
    ./bin/backup-db.sh -c;
    ```

2.  On the **new server** the files from the old server will be copied over with
    rsync. First step here is to stop the apps on the new server and remove the
    initial db and any generated test puzzles.

    ```bash
    cd /usr/local/src/puzzle-massive/;
    source bin/activate;
    sudo ./bin/puzzlectl.sh stop;
    rm /var/lib/puzzle-massive/sqlite3/db*;
    rm -rf /var/lib/puzzle-massive/archive/*
    rm -rf /srv/puzzle-massive/resources/*;
    sudo ./bin/clear_nginx_cache.sh;

    # do a `flushall` on the new server redis to clean out stuff
    redis-cli
    ```

3.  Copy the backup db (db-YYYY-MM-DD.dump.gz) to the new server and replace the
    other one (SQLITE_DATABASE_URI). This is assuming that ssh agent forwarding
    is enabled for the puzzle-blue host.

    ```bash
    cd /usr/local/src/puzzle-massive/;
    DBDUMPFILE="db-$(date --iso-8601 --utc).dump.gz";
    rsync --archive --progress --itemize-changes \
      dev@puzzle-blue:/usr/local/src/puzzle-massive/$DBDUMPFILE \
      /usr/local/src/puzzle-massive/;
    zcat $DBDUMPFILE | sqlite3 /var/lib/puzzle-massive/sqlite3/db
    cat db.dump.sql | sqlite3 /var/lib/puzzle-massive/sqlite3/db
    echo 'pragma journal_mode=wal' | sqlite3 /var/lib/puzzle-massive/sqlite3/db
    ```

4.  Copy the nginx logs (NGINXLOGDIR) found at: `/var/log/nginx/puzzle-massive/`

    ```bash
    rsync --archive --progress --itemize-changes \
      dev@puzzle-blue:/var/log/nginx/puzzle-massive \
      /var/log/nginx/
    ```

5.  Copy the archive directory (ARCHIVEDIR): `/var/lib/puzzle-massive/archive/`

    ```bash
    rsync --archive --progress --itemize-changes \
      dev@puzzle-blue:/var/lib/puzzle-massive/archive \
      /var/lib/puzzle-massive/
    ```

6.  Copy the resources directory (SRVDIR/resources) that contains the generated
    puzzles:

    ```bash
    rsync --archive --progress --itemize-changes \
      dev@puzzle-blue:/srv/puzzle-massive/resources \
      /srv/puzzle-massive/
    ```

7.  Run any migrate scripts if required for this version bump. Follow any other
    instructions for the migrate script if needed.

    ```bash
    python api/api/jobs/migrate_from_2_x.py site.cfg
    ```

8.  Start the new server and switch traffic over to it.

    After the old server data has been copied over, then start up the new server
    apps with the 'puzzlectl.sh' script. It is also good to monitor the logs to see
    if anything is throwing errors.

    ```
    cd /usr/local/src/puzzle-massive/;
    source bin/activate;
    sudo ./bin/puzzlectl.sh start;
    printf '' > /srv/puzzle-massive/root/puzzle-massive-message.html;
    sudo ./bin/log.sh;
    ```

    Verify that the new version of Puzzle Massive is running correctly on
    puzzle-green/. If everything checks out, then switch the traffic over to
    puzzle.massive.xyz/.

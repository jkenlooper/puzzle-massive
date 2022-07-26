# Deployment Guide

**DEPRECATED: Deployments are now done via Terraform and Ansible. See the `_infra/README.md`**

There are two kinds of deployments outlined here. The first one is for in-place
deployments where only minor changes are needed and the risk is low. The other
type of deployment is commonly called a blue-green deployment where a new server
is created and then when everything has been deployed and ready; traffic is
directed to the new server.

## Create a new version for the deployment

Deployments should use a versioned distribution file that is uploaded to the
server. This file can be made after a new version has been set in the
package.json.

```bash
cd client-side-public && make && cd -
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

**Either follow the steps outlined below _or_ use the quick-deploy.sh script to do an
in-place deployment.**

```bash
cd /usr/local/src/puzzle-massive;
sudo ./bin/quick-deploy.sh /home/dev/puzzle-massive-2.x.x.tar.gz
```

### Steps

1.  Stop the running apps and backup the db. The deactivate command is done to
    deactivate the python virtual environment. A backup of the database is made just as
    a cautionary measure and is left in the folder. The backup.sh script
    also moves data out of redis and into the database.

    ```bash
    cd /usr/local/src/puzzle-massive;
    source bin/activate;
    printf 'Updating...' > /srv/puzzle-massive/root/puzzle-massive-message.html;
    sudo ./bin/appctl.sh stop;
    sudo systemctl start puzzle-massive-api;
    sudo ./bin/clear_nginx_cache.sh;
    ./bin/backup.sh -c;
    sudo systemctl stop puzzle-massive-api;
    deactivate;
    ```

2.  Replace the current source code with the new version. Example shows the
    puzzle-massive-2.0.0.tar.gz which should be in the dev home directory. The
    current source code is moved to the home directory under a date label in
    case it needs to revert back. The `.env` file is copied
    over since it is not included in the distribution. The `.has-certs` file
    will signal if the site is setup for SSL (https://).

    ```bash
    cd /home/dev/;
    sudo mv /usr/local/src/puzzle-massive puzzle-massive-$(date +%F);
    sudo tar --directory=/usr/local/src/ --extract --gunzip -f puzzle-massive-2.0.0.tar.gz
    sudo chown -R dev:dev /usr/local/src/puzzle-massive
    cp puzzle-massive-$(date +%F)/.env /usr/local/src/puzzle-massive/;

    # Add .has-certs file if site has already been setup with bin/provision-certbot.sh
    cp puzzle-massive-$(date +%F)/.has-certs /usr/local/src/puzzle-massive/ || echo "No certs?";
    ```

3.  Make the new apps and install the source code. The install will also start
    everything back up. The last command to test and reload nginx is optional
    and is only needed if the nginx conf changed.

    ```bash
    cd /usr/local/src/puzzle-massive;
    python -m venv .;
    source bin/activate;
    make ENVIRONMENT=production;

    # Update any bit icon authors and add new bit icons if applicable
    python api/api/jobs/insert-or-replace-bit-icons.py

    # Update the enabled puzzle features if applicable
    python api/api/update_enabled_puzzle_features.py

    sudo make ENVIRONMENT=production install;
    sudo nginx -t;
    sudo systemctl reload nginx;
    printf '' > /srv/puzzle-massive/root/puzzle-massive-message.html;
    sudo ./bin/clear_nginx_cache.sh;
    ```

4.  Verify that stuff is working by monitoring the logs.

    ```bash
    sudo ./bin/appctl.sh status;
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

3.  SSH in as the dev user and upload or create the `.env` file
    in the `/usr/local/src/puzzle-massive/` directory. See the README on how to
    create it. At this point there is no need to SSH in to the server as the
    root user.

4.  Copy the certificates listed on the old server (`sudo certbot certificates`)
    to the new server. Skip this step if there is no old server to copy from.
    Note that these should be first copied from the old server to the dev home
    directory. Note that this step is to just prevent downtime and the
    /etc/letsencrypt/live/puzzle.massive.xyz/ directory will be removed when
    running the bin/provision-certbot.sh script.

    ```bash
    sudo mkdir -p /etc/letsencrypt/live/puzzle.massive.xyz/
    scp \
      dev@puzzle-massive-blue:/home/dev/fullchain.pem \
      /home/dev/
    sudo cp /home/dev/fullchain.pem /etc/letsencrypt/live/puzzle.massive.xyz/
    scp \
      dev@puzzle-massive-blue:/home/dev/privkey.pem \
      /home/dev/
    sudo cp /home/dev/privkey.pem /etc/letsencrypt/live/puzzle.massive.xyz/
    scp \
      dev@puzzle-massive-blue:/usr/local/src/puzzle-massive/.has-certs \
      /usr/local/src/puzzle-massive/
    ```

5.  Now create the initial bare-bones version without any data as the dev user.

    ```bash
    cd /usr/local/src/puzzle-massive/;
    python -m venv .;
    source bin/activate;
    make ENVIRONMENT=production;
    sudo make ENVIRONMENT=production install;
    sudo ./bin/appctl.sh stop -f;

    # should be run as 'dev' user
    python api/api/create_database.py site.cfg;

    # Update any bit icon authors and add new bit icons if applicable
    python api/api/jobs/insert-or-replace-bit-icons.py

    # Update the enabled puzzle features
    python api/api/update_enabled_puzzle_features.py

    sudo ./bin/appctl.sh start;
    ```

6.  The logs can be followed with the `./bin/log.sh` command. It is just
    a shortcut to doing the same with `journalctrl`.

    Check the status of the apps with this convenience command to `systemctl`.

    ```bash
    sudo ./bin/appctl.sh status;
    ```

7.  Test and reload the nginx config. If this is a new server you may need to
    remove the `/etc/nginx/sites-enabled/default` or
    `/etc/nginx/conf.d/default.conf` file. This site will include it's own
    [web/default.nginx.conf]().

    ```bash
    sudo nginx -t;
    sudo systemctl reload nginx
    ```

8.  Generate some random data and test.

    ```bash
    puzzle-massive-testdata players --count=100;

    puzzle-massive-testdata puzzles --count=2 --min-pieces=200 --pieces=900 --size=1800x1300\!;
    puzzle-massive-testdata puzzles --count=2 --min-pieces=200 --pieces=900 --size=800x1500\!;
    puzzle-massive-testdata puzzles --count=1 --pieces=2000 --size=3800x3500\!;
    puzzle-massive-testdata puzzles --count=30 --pieces=9 --size=180x180\!;

    puzzle-massive-testdata instances --count=10 --min-pieces=9 --pieces=50;
    ```

Note that by default the production version of the nginx conf for the website is
hosted at [puzzle.massive.xyz](http://puzzle.massive.xyz) as well as
[puzzle-massive-blue](http://puzzle-massive-blue/) and
[puzzle-massive-green](http://puzzle-massive-green/). You can edit
your `/etc/hosts` to point to the old (puzzle-massive-blue) and new
(puzzle-massive-green) servers.

### Transferring data from the old server to the new server

At this point two servers should be running the website with only the older
one (blue) having traffic. The new one (green) should be verified that everything is working
correctly by doing some integration testing. The next step is to stop the apps
on the old server and copy all the data over to the new puzzle-massive-green server.

1.  On the **new server** (puzzle-massive-green) the files from the old server will be copied over with
    rsync. First step here is to stop the apps on the new server and remove the
    initial db and any generated test puzzles.

    ```bash
    cd /usr/local/src/puzzle-massive/;
    source bin/activate;
    sudo ./bin/appctl.sh stop -f;
    rm /var/lib/puzzle-massive/sqlite3/db*;
    rm -rf /var/lib/puzzle-massive/archive/*
    rm -rf /srv/puzzle-massive/resources/*;
    sudo ./bin/clear_nginx_cache.sh;

    # Use `flushdb` on the new server to remove all keys on the redis database.
    REDIS_DB=$(./bin/puzzle-massive-site-cfg-echo site.cfg REDIS_DB);
    redis-cli -n ${REDIS_DB} flushdb
    ```

2.  Copy the nginx logs (NGINXLOGDIR) found at: `/var/log/nginx/puzzle-massive/`

    ```bash
    rsync --archive --progress --itemize-changes \
      dev@puzzle-massive-blue:/var/log/nginx/puzzle-massive \
      /var/log/nginx/
    ```

3.  Copy the archive directory (ARCHIVEDIR): `/var/lib/puzzle-massive/archive/`

    ```bash
    rsync --archive --progress --itemize-changes \
      dev@puzzle-massive-blue:/var/lib/puzzle-massive/archive \
      /var/lib/puzzle-massive/
    ```

4.  Copy the resources directory (SRVDIR/resources) that contains the generated
    puzzles:

    ```bash
    rsync --archive --progress --itemize-changes \
      dev@puzzle-massive-blue:/srv/puzzle-massive/resources \
      /srv/puzzle-massive/
    ```

Switch back to the **old server** (puzzle-massive-blue).

1.  On the **old server** (puzzle-massive-blue) stop the apps and backup the data. The old
    server is left untouched in case something fails on the new server.

    ```bash
    cd /usr/local/src/puzzle-massive/;
    source bin/activate;
    printf 'Updating...' > /srv/puzzle-massive/root/puzzle-massive-message.html;
    sudo ./bin/appctl.sh stop;
    sudo ./bin/clear_nginx_cache.sh;
    ./bin/puzzle-massive-api serve &
    ./bin/backup.sh -c;
    fg # and ctrl-c to stop the puzzle-massive-api serve process
    ```

Switch over to the **new server** (puzzle-massive-green).

1.  On the **new server** (puzzle-massive-green) the resource files from the old
    server will be copied over again now that the new server is down.

    Copy the backup db (db-YYYY-MM-DD.dump.gz) to the new server and replace the
    other one (SQLITE_DATABASE_URI). This is assuming that ssh agent forwarding
    is enabled for the puzzle-massive-blue host.

    ```bash
    rsync --archive --progress --itemize-changes \
      dev@puzzle-massive-blue:/var/log/nginx/puzzle-massive \
      /var/log/nginx/
    rsync --archive --progress --itemize-changes \
      dev@puzzle-massive-blue:/var/lib/puzzle-massive/archive \
      /var/lib/puzzle-massive/
    rsync --archive --progress --itemize-changes \
      dev@puzzle-massive-blue:/srv/puzzle-massive/resources \
      /srv/puzzle-massive/

    cd /usr/local/src/puzzle-massive/;
    source bin/activate;
    DBDUMPFILE="db-$(date +%F).dump.gz";
    rsync --archive --progress --itemize-changes \
      dev@puzzle-massive-blue:/usr/local/src/puzzle-massive/$DBDUMPFILE \
      /usr/local/src/puzzle-massive/;
    touch /var/lib/puzzle-massive/sqlite3/db
    zcat $DBDUMPFILE | sqlite3 /var/lib/puzzle-massive/sqlite3/db
    cat db.dump.sql | sqlite3 /var/lib/puzzle-massive/sqlite3/db
    echo 'pragma journal_mode=wal' | sqlite3 /var/lib/puzzle-massive/sqlite3/db

    # Run any migrate scripts needed for this version update if applicable
    python api/api/jobs/migrate_puzzle_massive_database_version.py

    # Update any bit icon authors and add new bit icons
    python api/api/jobs/insert-or-replace-bit-icons.py

    # Update the enabled puzzle features
    python api/api/update_enabled_puzzle_features.py
    ```

2.  Start the new server and switch traffic over to it.

    After the old server data has been copied over, then start up the new server
    apps with the 'bin/appctl.sh' script. It is also good to monitor the logs to see
    if anything is throwing errors.

    ```
    cd /usr/local/src/puzzle-massive/;
    source bin/activate;
    sudo ./bin/appctl.sh start;
    printf '' > /srv/puzzle-massive/root/puzzle-massive-message.html;
    sudo ./bin/log.sh;
    ```

    Verify that the new version of the website is running correctly on
    puzzle-massive-green/. If everything checks out, then switch the traffic over to
    puzzle.massive.xyz/.

3.  Set up the production server with TLS certs. [certbot](https://certbot.eff.org/)
    is used to deploy [Let's Encrypt](https://letsencrypt.org/) certificates.
    This will initially fail if the server isn't accepting traffic at the domain
    name.

    ```bash
    cd /usr/local/src/puzzle-massive/;
    source bin/activate;
    # Running make and make install can be skipped if .has-certs file exists
    skip_make=$(test -e .has-certs && echo 1)
    sudo bin/provision-certbot.sh /srv/puzzle-massive/
    if [ ! -n "$skip_make" ]; then
        make ENVIRONMENT=production;
        sudo make ENVIRONMENT=production install;
    fi
    sudo nginx -t;
    sudo systemctl reload nginx
    ```

## Removing the app from a server

Run the below commands to remove puzzle-massive from the
server. This will uninstall and disable the services, remove any files
installed outside of the `/usr/local/src/puzzle-massive/`
directory including the sqlite3 database and finally remove the source files as
well. _Only do this if the website is running on the new server and is no
longer needed on the old one._

```bash
cd /usr/local/src/puzzle-massive/;
source bin/activate;
sudo ./bin/appctl.sh stop;

# Removes any installed files outside of the project
sudo make uninstall;

# Remove files generated by make
make clean;
deactivate;

# Removes all data including the sqlite3 database
sudo rm -rf /var/lib/puzzle-massive/

# Remove the source files
cd ../;
sudo rm -rf /usr/local/src/puzzle-massive/;
```

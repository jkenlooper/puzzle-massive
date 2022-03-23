# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure(2) do |config|
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://atlas.hashicorp.com/search.
  config.vm.box = "bento/ubuntu-20.04"

  config.vm.define "legacy_puzzle_massive", primary: true do |legacy_puzzle_massive|
    legacy_puzzle_massive.vm.hostname = "puzzle.massive.test"
    legacy_puzzle_massive.vm.network :private_network, ip: "192.168.56.24", auto_config: true, hostname: true

    # p + u + z + z + l + e + 38000 = 38682
    legacy_puzzle_massive.vm.network "forwarded_port", guest: 80, host: 38682, auto_correct: false
    legacy_puzzle_massive.vm.network "forwarded_port", guest: 443, host: 38683, auto_correct: false

    legacy_puzzle_massive.vm.provider "virtualbox" do |vb|
      vb.memory = "4096"
      vb.cpus = 2
    end

    legacy_puzzle_massive.vm.post_up_message = <<-POST_UP_MESSAGE
      Please run the below command to initialize the instance if haven't done so yet.

      vagrant provision --provision-with shell-init-dev-local

      This can be run multiple times to update things as needed.
      See further documentation in docs/development.md
    POST_UP_MESSAGE

    legacy_puzzle_massive.trigger.before [:halt, :destroy] do |trigger|
      trigger.warn = "Stop app and create backup db to shared directory on host _infra/local/output/db.dump.gz"
      trigger.on_error = :continue
      trigger.run_remote = {inline: <<-SHELL
        bash -c 'cd /usr/local/src/puzzle-massive/ && ./bin/appctl.sh start && ./bin/appctl.sh stop && rsync -av /home/dev/db-$(date --iso-8601 --utc).dump.gz /home/vagrant/output/db.dump.gz'
      SHELL
      }
    end
    legacy_puzzle_massive.trigger.before :destroy do |trigger|
      trigger.warn = "Preserving puzzle massive resources data to shared directory on host _infra/local/output/resources"
      trigger.on_error = :continue
      trigger.run_remote = {inline: <<-SHELL
        bash -c 'rsync -a /srv/puzzle-massive/resources /home/vagrant/output'
      SHELL
      }
    end

    legacy_puzzle_massive.trigger.after :up do |trigger|
      trigger.info = "Checking status of running services"
      trigger.on_error = :continue
      trigger.run_remote = {inline: <<-SHELL
        bash -c 'nginx -t;
        systemctl is-active nginx;
        cd /usr/local/src/puzzle-massive;
        ./bin/appctl.sh is-active;'
      SHELL
      }
    end

    # In case the bin/create_dot_env.sh wasn't run on the local machine.
    legacy_puzzle_massive.vm.provision "shell-auto-create-dot-env", type: "shell", run: "always", inline: <<-SHELL
      if test ! -e /home/vagrant/puzzle-massive/.env; then
        cat <<-'DEFAULT_ENV' > /home/vagrant/puzzle-massive/.env;
UNSPLASH_APPLICATION_ID=''
UNSPLASH_APPLICATION_NAME=''
UNSPLASH_SECRET=''
NEW_PUZZLE_CONTRIB='rizzo'
SECURE_COOKIE_SECRET='chocolate chip'
SUGGEST_IMAGE_LINK=''
CLIENT_MAX_BODY_SIZE__PUZZLE_UPLOAD='100m'
CLIENT_MAX_BODY_SIZE__ADMIN_PUZZLE_PROMOTE_SUGGESTED='200m'
SMTP_HOST='localhost'
SMTP_PORT='587'
SMTP_USER='user@localhost'
SMTP_PASSWORD='somepassword'
EMAIL_SENDER='sender@localhost'
EMAIL_MODERATOR='moderator@localhost'
AUTO_APPROVE_PUZZLES='y'
LOCAL_PUZZLE_RESOURCES='n'
CDN_BASE_URL='http://localhost:38685'
PUZZLE_RESOURCES_BUCKET_REGION='local'
PUZZLE_RESOURCES_BUCKET_ENDPOINT_URL='http://s3fake.puzzle.massive.test:4568'
PUZZLE_RESOURCES_BUCKET='chum'
PUZZLE_RESOURCES_BUCKET_OBJECT_CACHE_CONTROL='public, max-age:31536000, immutable'
EPHEMERAL_ARCHIVE_ENDPOINT_URL=''
EPHEMERAL_ARCHIVE_BUCKET=''
PUZZLE_RULES="all"
PUZZLE_FEATURES="all"
BLOCKEDPLAYER_EXPIRE_TIMEOUTS="30 300 3600"
MINIMUM_PIECE_COUNT=20
MAXIMUM_PIECE_COUNT=50000
PUZZLE_PIECE_GROUPS="100 200 400 800 1600 2200 4000 60000"
ACTIVE_PUZZLES_IN_PIECE_GROUPS="40  20  10  10  5    5    5    5"
MINIMUM_IN_QUEUE_PUZZLES_IN_PIECE_GROUPS="6   6   2   2   1    1    0    0"
MAX_POINT_COST_FOR_REBUILDING=1000
MAX_POINT_COST_FOR_DELETING=1000
BID_COST_PER_PUZZLE=100
POINT_COST_FOR_CHANGING_BIT=100
POINT_COST_FOR_CHANGING_NAME=100
NEW_USER_STARTING_POINTS=1300
POINTS_CAP=15000
REWARD_INSTANCE_SLOT_SCORE_THRESHOLD=1
BIT_ICON_EXPIRATION="
0:    20 minutes,
1:    1 day,
50:   3 days,
400:  7 days,
800:  14 days,
1600: 1 months
"
PUBLISH_WORKER_COUNT=2
STREAM_WORKER_COUNT=2
DOMAIN_NAME="puzzle.massive.test"
SITE_TITLE="Local Puzzle Massive"
HOME_PAGE_ROUTE="/chill/site/front/"
SOURCE_CODE_LINK="https://github.com/jkenlooper/puzzle-massive/"
M3=""
DEFAULT_ENV
      fi
    SHELL

    legacy_puzzle_massive.vm.provision "shell-etc-hosts", type: "shell", inline: <<-SHELL
      echo "192.168.56.26 s3fake.puzzle.massive.test" >> /etc/hosts
    SHELL

    # The add-dev-user.sh will need to copy the /root/.ssh/authorized_keys file to
    # the /home/dev/.ssh/ directory.  On a vagrant virtual machine; this file
    # doesn't exist in the /root/ directory.
    legacy_puzzle_massive.vm.provision "shell-prep-root", type: "shell", inline: <<-SHELL
      cp -r /home/vagrant/.ssh /root/
    SHELL

    # For vagrant, set up the dev user and the initial
    # /usr/local/src/puzzle-massive directory.
    # To do db stuff as dev use `sudo su dev`.
    legacy_puzzle_massive.vm.provision "bin-add-dev-user", type: "shell", path: "bin/add-dev-user.sh", args: 'vagrant'
    legacy_puzzle_massive.vm.provision "bin-update-sshd-config", type: "shell", path: "bin/update-sshd-config.sh"
    legacy_puzzle_massive.vm.provision "bin-set-external-puzzle-massive-in-hosts", type: "shell", path: "bin/set-external-puzzle-massive-in-hosts.sh"
    legacy_puzzle_massive.vm.provision "bin-install-latest-stable-nginx", type: "shell", path: "bin/install-latest-stable-nginx.sh"
    legacy_puzzle_massive.vm.provision "bin-setup", type: "shell", path: "bin/setup.sh"
    # Skip setting iptables for vagrant VMs
    #legacy_puzzle_massive.vm.provision "bin-iptables-setup-firewall", type: "shell", path: "bin/iptables-setup-firewall.sh"

    legacy_puzzle_massive.vm.provision "bin-provision-local-ssl-certs", privileged: true, type: "shell", inline: <<-SHELL
      cd /home/vagrant/puzzle-massive
      #test -e /home/vagrant/output/localhost-CA.key && cp /home/vagrant/output/localhost-CA.key /home/dev/
      #&& chown dev:dev /home/dev/localhost-CA.key
      #test -e /home/vagrant/output/localhost-CA.pem && cp /home/vagrant/output/localhost-CA.pem /home/dev/
      #&& chown dev:dev /home/dev/localhost-CA.pem
      #touch web/localhost.key web/localhost.crt
      #chown dev:dev web/localhost.key web/localhost.crt
      ./bin/provision-local-ssl-certs.sh -k /home/vagrant/output/localhost-CA.key -p /home/vagrant/output/localhost-CA.pem
    SHELL

    # The devsync.sh uses local-puzzle-massive when syncing files
    # the devsync.sh depends on watchpack which will require nodejs
    legacy_puzzle_massive.vm.provision "shell-local-devsync-support", type: "shell", inline: <<-SHELL
      curl -sL https://deb.nodesource.com/setup_14.x | sudo -E bash -
      apt-get install -y nodejs
      echo "127.0.0.1 local-puzzle-massive" >> /etc/hosts
    SHELL

    legacy_puzzle_massive.vm.provision "shell-vagrant-local-ssh", privileged: false, type: "shell", inline: <<-SHELL
      ssh-keyscan -H local-puzzle-massive >> /home/vagrant/.ssh/known_hosts
      ssh-keygen -t rsa -C "vagrant@local-puzzle-massive" -N "" -q -f /home/vagrant/.ssh/id_rsa
    SHELL
    legacy_puzzle_massive.vm.provision "shell-vagrant-local-ssh-part-two", type: "shell", inline: <<-SHELL
      cat /home/vagrant/.ssh/id_rsa.pub >> /home/dev/.ssh/authorized_keys
    SHELL

    # bin/distwatch.js depends on watchpack
    legacy_puzzle_massive.vm.provision "shell-vagrant-npm-install-and-build", privileged: false, type: "shell", inline: <<-SHELL
      cd /home/vagrant/puzzle-massive
      npm install --ignore-scripts watchpack@2.2.0
    SHELL

    legacy_puzzle_massive.vm.provision "shell-usr-local-src-puzzle-massive", type: "shell", inline: <<-SHELL
      mkdir -p /usr/local/src/puzzle-massive;
      chown dev:dev /usr/local/src/puzzle-massive;
    SHELL

    legacy_puzzle_massive.vm.provision "shell-vagrant-devsync", privileged: false, type: "shell", inline: <<-SHELL
      cd /home/vagrant/puzzle-massive
      ./bin/devsync.sh
    SHELL

    legacy_puzzle_massive.vm.provision "shell-services-devsync", type: "shell", inline: <<-SHELL
      /home/vagrant/puzzle-massive/_infra/local/local-puzzle-massive-auto-devsync.service.sh vagrant > /etc/systemd/system/local-puzzle-massive-auto-devsync.service
      systemctl start local-puzzle-massive-auto-devsync
      systemctl enable local-puzzle-massive-auto-devsync

      systemctl daemon-reload
    SHELL

    legacy_puzzle_massive.vm.provision "shell-setup-nginx-vagrant", type: "shell", inline: <<-SHELL
      touch /etc/nginx/allow_deny_admin.nginx.conf
    SHELL

    # BASIC_AUTH_USER=$(read -p 'username: ' && echo $REPLY) BASIC_AUTH_PASSPHRASE=$(read -sp 'passphrase: ' && echo $REPLY) vagrant provision --provision-with add-user-to-basic-auth
    legacy_puzzle_massive.vm.provision "add-user-to-basic-auth", type: :ansible_local, run: "never" do |ansible|
      ansible.playbook = "_infra/ansible-playbooks/add-user-to-basic-auth.yml"
      ansible.verbose = false
      ansible.extra_vars = {
        user: ENV["BASIC_AUTH_USER"] || '',
        passphrase: ENV["BASIC_AUTH_PASSPHRASE"] || ''
      }
    end

    legacy_puzzle_massive.vm.provision "appctl-stop", type: :ansible_local, run: "never" do |ansible|
      ansible.playbook = "_infra/ansible-playbooks/appctl-stop.yml"
      ansible.verbose = false
      ansible.extra_vars = {
        message_file: ENV["MESSAGE_FILE"] || '../../root/puzzle-massive-message.html',
      }
    end
    legacy_puzzle_massive.vm.provision "appctl-start", type: :ansible_local, run: "never" do |ansible|
      ansible.playbook = "_infra/ansible-playbooks/appctl-start.yml"
      ansible.verbose = false
    end


    # This requires ansible to be on the host machine since it reboots the
    # controlling node (can't use ansible_local here).
    legacy_puzzle_massive.vm.provision "update-packages-and-reboot", type: :ansible, run: "never" do |ansible|
      ansible.playbook = "_infra/ansible-playbooks/update-packages-and-reboot.yml"
      ansible.verbose = false
      ansible.extra_vars = {
        message_file: ENV["MESSAGE_FILE"] || '../../root/puzzle-massive-message.html',
      }
    end

    legacy_puzzle_massive.vm.provision "in-place-quick-deploy", type: :ansible_local, run: "never" do |ansible|
      ansible.playbook = "_infra/ansible-playbooks/in-place-quick-deploy.yml"
      ansible.verbose = "vvv"
      #ansible.verbose = false
      ansible.extra_vars = {
        makeenvironment: 'development',
        dist_file: ENV["DIST_FILE"],
        message_file: ENV["MESSAGE_FILE"] || '../../root/puzzle-massive-message.html',
      }
    end

    legacy_puzzle_massive.vm.provision "shell-set-s3fake-aws-bucket-credentials", type: "shell", inline: <<-SHELL
    mkdir -p /home/dev/.aws
    cat <<-'AWS_CREDENTIALS_APP' > /home/dev/.aws/credentials
[default]
aws_access_key_id = S3RVER
aws_secret_access_key = S3RVER
AWS_CREDENTIALS_APP
    chmod 0600 /home/dev/.aws/credentials
    cat <<-'AWS_CONFIG_APP' > /home/dev/.aws/config
[default]
region = local
AWS_CONFIG_APP
    chmod 0600 /home/dev/.aws/config
    chown -R dev:dev /home/dev/.aws
    SHELL

    # This provisioning script is idempotent.
    legacy_puzzle_massive.vm.provision "shell-init-dev-local",
      type: "shell",
      run: "never",
      inline: <<-SHELL
        cd /usr/local/src/puzzle-massive;
        touch .vagrant-overrides
        chown dev:dev .vagrant-overrides
        echo "Stopping the app and creating a backup db file"
        ./bin/appctl.sh stop;
        su --command '
          python -m venv .;
          rm -f site.cfg
          make;
        ' dev
        make install;
        ./bin/appctl.sh stop -f;
        su --command '
          ./bin/python api/api/create_database.py site.cfg \
            || echo "The api/api/create_database.py failed execution. Assuming that sqlite database tables already exists."
          ./bin/python api/api/jobs/migrate_puzzle_massive_database_version.py
          ./bin/python api/api/jobs/insert-or-replace-bit-icons.py;
          ./bin/python api/api/update_enabled_puzzle_features.py;
        ' dev
        nginx -t;
        systemctl reload nginx;
        ./bin/appctl.sh start;
        ./bin/appctl.sh status;
        systemctl status nginx;
        ./bin/appctl.sh is-active;
        systemctl is-active nginx;
      SHELL

    legacy_puzzle_massive.vm.provision "shell-testdata-puzzles-quick", type: "shell", run: "never", inline: <<-SHELL
      cd /usr/local/src/puzzle-massive;
      su --command '
        ./bin/puzzle-massive-testdata players --count=100;
        ./bin/puzzle-massive-testdata puzzles --count=10 --pieces=20 --size=800x800\!;
        ./bin/puzzle-massive-testdata puzzles --count=1 --pieces=100 --size=1800x800\!;
        ./bin/puzzle-massive-testdata puzzles --count=1 --pieces=100 --size=1800x1800\!;
        ./bin/puzzle-massive-testdata puzzles --count=1 --pieces=100 --size=800x1800\!;
        ./bin/puzzle-massive-testdata puzzles --count=1 --pieces=900 --size=6720x4480\!;
        ./bin/puzzle-massive-scheduler --task UpdatePuzzleQueue;
      ' dev
    SHELL

    legacy_puzzle_massive.vm.provision "shell-testdata-puzzles", type: "shell", run: "never", inline: <<-SHELL
      cd /usr/local/src/puzzle-massive;
      su --command '
        ./bin/puzzle-massive-testdata players --count=100;
        ./bin/puzzle-massive-testdata puzzles --count=10 --min-pieces=20 --pieces=400 --size=1800x800\!;
        ./bin/puzzle-massive-testdata puzzles --count=10 --min-pieces=20 --pieces=400 --size=1800x1800\!;
        ./bin/puzzle-massive-testdata puzzles --count=10 --min-pieces=20 --pieces=400 --size=800x1800\!;
        ./bin/puzzle-massive-testdata puzzles --count=10 --min-pieces=40 --pieces=90 --size=4800x800\!;
        ./bin/puzzle-massive-testdata puzzles --count=10 --min-pieces=40 --pieces=90 --size=800x4800\!;
        ./bin/puzzle-massive-testdata puzzles --count=3 --min-pieces=400 --pieces=1900 --size=5040x3360\!;
        ./bin/puzzle-massive-testdata puzzles --count=3 --min-pieces=400 --pieces=1900 --size=4000x5000\!;
        ./bin/puzzle-massive-testdata puzzles --count=3 --min-pieces=400 --pieces=1900 --size=5212x6741\!;
        ./bin/puzzle-massive-testdata puzzles --count=3 --min-pieces=400 --pieces=1900 --size=6720x4480\!;
        ./bin/puzzle-massive-testdata puzzles --count=3 --min-pieces=1900 --pieces=3900 --size=5040x3360\!;
        ./bin/puzzle-massive-testdata puzzles --count=3 --min-pieces=1900 --pieces=3900 --size=4000x5000\!;
        ./bin/puzzle-massive-testdata puzzles --count=3 --min-pieces=1900 --pieces=3900 --size=5212x6741\!;
        ./bin/puzzle-massive-testdata puzzles --count=3 --min-pieces=1900 --pieces=3900 --size=6720x4480\!;
        ./bin/puzzle-massive-scheduler --task UpdatePuzzleQueue;
      ' dev
    SHELL

    legacy_puzzle_massive.vm.provision "sync-legacy-puzzle-massive-resources-directory-from-local", type: :ansible, run: "never" do |ansible|
      ansible.playbook = "_infra/ansible-playbooks/sync-legacy-puzzle-massive-resources-directory-from-local.yml"
      ansible.verbose = "vvv"
      #ansible.verbose = false
      ansible.extra_vars = {
        resources_directory: ENV["RESOURCES_DIRECTORY"] || '../local/output/resources'
      }
    end

    # Syncing to local happens automatically via the Vagrant triggers for 'halt' and 'destroy'.
    legacy_puzzle_massive.vm.provision "sync-legacy-puzzle-massive-resources-directory-to-local", type: :ansible, run: "never" do |ansible|
      ansible.playbook = "_infra/ansible-playbooks/sync-legacy-puzzle-massive-resources-directory-to-local.yml"
      ansible.extra_vars = {
        resources_directory: ENV["RESOURCES_DIRECTORY"] || '../local/output/resources'
      }
    end

    legacy_puzzle_massive.vm.provision "restore-db-on-legacy-puzzle-massive", type: :ansible_local, run: "never" do |ansible|
      ansible.playbook = "_infra/ansible-playbooks/restore-db-on-legacy-puzzle-massive.yml"
      ansible.verbose = "vvv"
      #ansible.verbose = false
      ansible.extra_vars = {
        message_file: ENV["MESSAGE_FILE"] || '../../root/puzzle-massive-message.html',
        db_dump_file: ENV["DB_DUMP_FILE"] || '../local/output/db.dump.gz'
      }
    end

  end

  config.vm.define "cdn" do |cdn|
    cdn.vm.hostname = "cdn.puzzle.massive.test"
    cdn.vm.network :private_network, ip: "192.168.56.25", auto_config: true, hostname: true

    cdn.vm.network "forwarded_port", guest: 80, host: 38685, auto_correct: false

    cdn.vm.provider "virtualbox" do |vb|
      vb.memory = "1024"
      vb.cpus = 1
    end

    cdn.vm.provision "shell-etc-hosts", type: "shell", inline: <<-SHELL
    echo "192.168.56.26 s3fake.puzzle.massive.test" >> /etc/hosts
    SHELL

    cdn.vm.provision "bin-update-sshd-config", type: "shell", path: "bin/update-sshd-config.sh"
    cdn.vm.provision "bin-install-latest-stable-nginx", type: "shell", path: "bin/install-latest-stable-nginx.sh"
    # Skip setting iptables for vagrant VMs
    #cdn.vm.provision "bin-iptables-setup-firewall", type: "shell", path: "bin/iptables-setup-firewall.sh"

    cdn.vm.provision "shell-install-nginx-conf", type: "shell", inline: <<-SHELL
    mkdir -p /etc/nginx/snippets
    echo "server_name localhost;" > /etc/nginx/snippets/server_name-cdn.nginx.conf
    echo "proxy_pass http://s3fake.puzzle.massive.test:4568/chum/resources/;" > /etc/nginx/snippets/proxy_pass-cdn.nginx.conf
    cat <<-SNIPPET > /etc/nginx/snippets/ssl_certificate-ssl_certificate_key-cdn.nginx.conf
      #listen 443 ssl http2;
      #ssl_certificate /etc/nginx/ssl/localhost.crt;
      #ssl_certificate_key /etc/nginx/ssl/localhost.key;
SNIPPET
    cp /home/vagrant/puzzle-massive/web/cdn.nginx.conf /etc/nginx/nginx.conf

    mkdir -p /var/lib/cdn/cache/
    chown -R nginx:nginx /var/lib/cdn/cache/
    mkdir -p /var/log/nginx/puzzle-massive/
    chown -R nginx:nginx /var/log/nginx/puzzle-massive/

    # TODO: setup service to manage blocked_ip.conf from the admin site.
    touch /etc/nginx/blocked_ip.conf

    nginx -t
    systemctl start nginx
    systemctl reload nginx
    SHELL

  end

  config.vm.define "s3fake" do |s3fake|
    s3fake.vm.hostname = "s3fake.puzzle.massive.test"
    s3fake.vm.network :private_network, ip: "192.168.56.26", auto_config: true, hostname: true
    s3fake.vm.network "forwarded_port", guest: 4568, host: 38686, auto_correct: false

    s3fake.vm.provider "virtualbox" do |vb|
      vb.memory = "1024"
      vb.cpus = 1
    end

    s3fake.trigger.before [:destroy, :halt] do |trigger|
      trigger.warn = "Preserving s3rver files to shared directory on host _infra/local/output/s3rver"
      trigger.on_error = :continue
      trigger.run_remote = {inline: <<-SHELL
        bash -c 'rsync -av /home/s3rver/files /home/vagrant/output/s3rver'
      SHELL
      }
    end
    s3fake.trigger.after :up do |trigger|
      trigger.warn = "Syncing s3rver files from shared directory on host _infra/local/output/s3rver"
      trigger.on_error = :continue
      trigger.run_remote = {inline: <<-SHELL
        mkdir -p /home/vagrant/output/s3rver/files
        bash -c 'rsync -av /home/vagrant/output/s3rver/files /home/s3rver/ && chown -R s3rver:s3rver /home/s3rver/files'
      SHELL
      }
    end

    s3fake.vm.provision "shell-install-s3rver", type: "shell", inline: <<-SHELL
    apt-get update
#&& black && eslint --cache --fix && stylelint --fix
    apt-get install -y nodejs npm

    adduser s3rver --disabled-login --disabled-password --gecos "" || echo 'user exists already?'

    su --command '
      cd /home/s3rver
      cat <<-PACKAGEJSON > package.json
{
  "name": "_",
  "version": "1.0.0",
  "description": "Fake S3 server",
  "scripts": {
    "start": "s3rver --directory /home/s3rver/files --address s3fake.puzzle.massive.test --no-vhost-buckets --configure-bucket chum"
  },
  "dependencies": {
    "s3rver": "3.7.1"
  }
}
PACKAGEJSON

      mkdir -p /home/s3rver/files
      npm install --no-save --ignore-scripts 2> /dev/null
    ' s3rver

    cat <<-'SERVICE_INSTALL' > /etc/systemd/system/s3rver.service
[Unit]
Description=Fake S3 Server
After=multi-user.target

[Service]
Type=exec
User=s3rver
Group=s3rver
WorkingDirectory=/home/s3rver
ExecStart=npm start
Restart=on-failure

[Install]
WantedBy=multi-user.target
SERVICE_INSTALL
    systemctl daemon-reload
    systemctl start s3rver
    systemctl enable s3rver

    SHELL

    s3fake.vm.post_up_message = <<-POST_UP_MESSAGE
      Fake S3 Server is running in the private network with a 'chum' bucket.
      Use these AWS credentials to connect to it:
        Access Key Id: "S3RVER"
        Secret Access Key: "S3RVER"

      # Example of uploading test-file and fetching it both with `aws s3 cp` and `curl`.
      echo 'testing' > test-file
      aws s3 cp --endpoint-url=http://192.168.56.26:38686 test-file s3://chum/
      aws s3 cp --endpoint-url=http://192.168.56.26:38686 s3://chum/test-file get-test-file
      curl http://192.168.56.26:38686/chum/test-file
    POST_UP_MESSAGE

  end

  # Disable the default /vagrant shared folder
  # Not disabling the /vagrant synced folder since ansible_local depends on it.
  config.vm.synced_folder ".", "/vagrant", disabled: false

  # The rsync arg '--delete' is not used here to prevent removing any generated
  # files from running 'make' command.
  config.vm.synced_folder ".", "/home/vagrant/puzzle-massive", type: "rsync",
    rsync__exclude: ["/.git/", "/.vagrant/", "/.terraform/", "/terraform.tfstate.d/", ".terraform.lock.hcl", "/node_modules/", "/include/", "/lib/", "/lib64/", "/local/", "/share/", "/_infra/local/output/", "/_infra/development/","/_infra/test/","/_infra/acceptance/","/_infra/production/", "/puzzle-massive-*.tar.gz", "/puzzle-massive-*.bundle"],
    rsync__args: ["--verbose", "--archive", "-z", "--copy-links", "--delay-updates"]

  config.vm.synced_folder "./_infra/local/output", "/home/vagrant/output"

end

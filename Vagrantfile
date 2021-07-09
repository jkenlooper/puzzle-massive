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

    legacy_puzzle_massive.vm.network "forwarded_port", guest: 80, host: 8080
    legacy_puzzle_massive.vm.network "forwarded_port", guest: 443, host: 8081

    legacy_puzzle_massive.vm.provider "virtualbox" do |vb|
      vb.memory = "4096"
      vb.cpus = 2
    end

    legacy_puzzle_massive.vm.post_up_message = <<-POST_UP_MESSAGE
      Please run the below command to initialize the instance if haven't done so yet.

      VAGRANT_FORWARDED_PORT_80=$(vagrant port --guest 80) vagrant provision --provision-with shell-init-dev-local

      See further documentation in docs/development.md
    POST_UP_MESSAGE

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
          SMTP_HOST='localhost'
          SMTP_PORT='587'
          SMTP_USER='user@localhost'
          SMTP_PASSWORD='somepassword'
          EMAIL_SENDER='sender@localhost'
          EMAIL_MODERATOR='moderator@localhost'
          AUTO_APPROVE_PUZZLES='y'
          LOCAL_PUZZLE_RESOURCES='y'
          CDN_BASE_URL=''
          PUZZLE_RESOURCES_BUCKET_REGION=''
          PUZZLE_RESOURCES_BUCKET_ENDPOINT_URL=''
          PUZZLE_RESOURCES_BUCKET=''
          PUZZLE_RESOURCES_BUCKET_OBJECT_CACHE_CONTROL=''
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
          DOMAIN_NAME="puzzle.massive.xyz"
          SITE_TITLE="Puzzle Massive"
          HOME_PAGE_ROUTE="/chill/site/front/"
          SOURCE_CODE_LINK="https://github.com/jkenlooper/puzzle-massive/"
          M3=""
DEFAULT_ENV
      fi
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
    legacy_puzzle_massive.vm.provision "bin-setup", type: "shell", path: "bin/setup.sh"

    # The devsync.sh uses local-puzzle-massive when syncing files
    # Install the watchit command that is used in _infra/local/watchit.sh script.
    legacy_puzzle_massive.vm.provision "shell-watchit-support", type: "shell", inline: <<-SHELL
      echo "127.0.0.1 local-puzzle-massive" >> /etc/hosts
      pip install watchit
    SHELL

    legacy_puzzle_massive.vm.provision "shell-vagrant-local-ssh", privileged: false, type: "shell", inline: <<-SHELL
      ssh-keyscan -H local-puzzle-massive >> /home/vagrant/.ssh/known_hosts
      ssh-keygen -t rsa -C "vagrant@local-puzzle-massive" -N "" -q -f /home/vagrant/.ssh/id_rsa
    SHELL
    legacy_puzzle_massive.vm.provision "shell-vagrant-local-ssh-part-two", type: "shell", inline: <<-SHELL
      cat /home/vagrant/.ssh/id_rsa.pub >> /home/dev/.ssh/authorized_keys
    SHELL

    legacy_puzzle_massive.vm.provision "shell-vagrant-npm-install-and-build", privileged: false, type: "shell", inline: <<-SHELL
      cd /home/vagrant/puzzle-massive
      npm install
      npm run debug
    SHELL

    legacy_puzzle_massive.vm.provision "shell-usr-local-src-puzzle-massive", type: "shell", inline: <<-SHELL
      mkdir -p /usr/local/src/puzzle-massive;
      chown dev:dev /usr/local/src/puzzle-massive;
    SHELL

    legacy_puzzle_massive.vm.provision "shell-vagrant-devsync", privileged: false, type: "shell", inline: <<-SHELL
      cd /home/vagrant/puzzle-massive
      ./bin/devsync.sh
    SHELL

    legacy_puzzle_massive.vm.provision "shell-services-watchit-devsync", type: "shell", inline: <<-SHELL
      /home/vagrant/puzzle-massive/_infra/local/local-puzzle-massive-watchit.service.sh vagrant > /etc/systemd/system/local-puzzle-massive-watchit.service
      systemctl start local-puzzle-massive-watchit
      systemctl enable local-puzzle-massive-watchit

      /home/vagrant/puzzle-massive/_infra/local/local-puzzle-massive-auto-devsync.service.sh vagrant > /etc/systemd/system/local-puzzle-massive-auto-devsync.service
      systemctl start local-puzzle-massive-auto-devsync
      systemctl enable local-puzzle-massive-auto-devsync
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


    # #example
    # legacy_puzzle_massive.vm.provision "playbook", type: :ansible_local, run: "always" do |ansible|
    #   ansible.playbook = "_infra/ansible-playbooks/main.yml"
    #   ansible.verbose = true
    #   ansible.extra_vars = {
    #     initial_dev_user_password: 'vagrant'
    #   }
    # end


    # This provisioning script is idempotent.
    legacy_puzzle_massive.vm.provision "shell-init-dev-local",
      type: "shell",
      run: "never",
      env: {
        "VAGRANT_FORWARDED_PORT_80": ENV["VAGRANT_FORWARDED_PORT_80"]
      },
      inline: <<-SHELL
        cd /usr/local/src/puzzle-massive;
        echo "VAGRANT_FORWARDED_PORT_80=$VAGRANT_FORWARDED_PORT_80" > .vagrant-overrides
        chown dev:dev .vagrant-overrides
        echo "Stopping the app and creating a backup db file"
        ./bin/appctl.sh stop;
        su --command '
          python -m venv .;
          make;
        ' dev
        make install;
        ./bin/appctl.sh stop -f;
        su --command '
          ./bin/python api/api/create_database.py site.cfg \
            || echo "The api/api/create_database.py failed execution. Assuming that sqlite database tables already exists."
          ./bin/python api/api/jobs/insert-or-replace-bit-icons.py;
          ./bin/python api/api/update_enabled_puzzle_features.py;
        ' dev
        nginx -t;
        systemctl reload nginx;
        ./bin/appctl.sh start;
        ./bin/appctl.sh status;
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
      ' dev
    SHELL

  end

  config.vm.define "cdn" do |cdn|

    cdn.vm.network "forwarded_port", guest: 80, host: 8082
    cdn.vm.network "forwarded_port", guest: 443, host: 8083

    cdn.vm.provider "virtualbox" do |vb|
      vb.memory = "1024"
      vb.cpus = 1
    end

  end

  # Disable the default /vagrant shared folder
  # Not disabling the /vagrant synced folder since ansible_local depends on it.
  config.vm.synced_folder ".", "/vagrant", disabled: false

  config.vm.synced_folder ".", "/home/vagrant/puzzle-massive", type: "rsync",
    rsync__exclude: ["/.git/", "/.vagrant/", "/.terraform/", "/terraform.tfstate.d/", ".terraform.lock.hcl", "/node_modules/", "/include/", "/lib/", "/lib64/", "/local/", "/share/", "/dist/", "/puzzle-massive-*.tar.gz", "/puzzle-massive-*.bundle"],
    rsync__args: ["--verbose", "--archive", "--delete", "-z", "--copy-links", "--delay-updates"]

  config.vm.synced_folder "./_infra/local/output", "/home/vagrant/output"

end

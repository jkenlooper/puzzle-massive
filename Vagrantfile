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

  # Disable automatic box update checking. If you disable this, then
  # boxes will only be checked for updates when the user runs
  # `vagrant box outdated`. This is not recommended.
  # config.vm.box_check_update = false

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine. In the example below,
  # accessing "localhost:8080" will access port 80 on the guest machine.
  config.vm.network "forwarded_port", guest: 80, host: 8080
  config.vm.network "forwarded_port", guest: 443, host: 8081

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  # config.vm.network "private_network", ip: "192.168.33.10"
  #config.vm.network "private_network", type: "dhcp"

  # Create a public network, which generally matched to bridged network.
  # Bridged networks make the machine appear as another physical device on
  # your network.
  # config.vm.network "public_network"

  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.
  # config.vm.synced_folder "../data", "/vagrant_data"

  # Disable the default /vagrant shared folder
  config.vm.synced_folder ".", "/vagrant", disabled: true

  config.vm.synced_folder ".", "/home/vagrant/puzzle-massive", type: "rsync",
    rsync__exclude: ["/.git/", "/.vagrant/", "/node_modules/", "/include/", "/lib/", "/lib64/", "/local/", "/share/", "/dist/", "/puzzle-massive-*.tar.gz"],
    rsync__args: ["--verbose", "--archive", "--delete", "-z", "--copy-links", "--delay-updates"]

  config.vm.synced_folder "./_infra/local/output", "/home/vagrant/output"

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # Example for VirtualBox:
  #
  config.vm.provider "virtualbox" do |vb|
    # Display the VirtualBox GUI when booting the machine
    # vb.gui = true

    # Customize the amount of memory on the VM:
    vb.memory = "4096"
    vb.cpus = 2
  end
  #
  # View the documentation for the provider you are using for more
  # information on available options.

  # Define a Vagrant Push strategy for pushing to Atlas. Other push strategies
  # such as FTP and Heroku are also available. See the documentation at
  # https://docs.vagrantup.com/v2/push/atlas.html for more information.
  # config.push.define "atlas" do |push|
  #   push.app = "YOUR_ATLAS_USERNAME/YOUR_APPLICATION_NAME"
  # end

  # Enable provisioning with a shell script. Additional provisioners such as
  # Puppet, Chef, Ansible, Salt, and Docker are also available. Please see the
  # documentation for more information about their specific syntax and use.
  # config.vm.provision "shell", inline: <<-SHELL
  #   sudo apt-get update
  #   sudo apt-get install -y apache2
  # SHELL

  # For vagrant just set up the dev user and the initial
  # /usr/local/src/puzzle-massive directory.
  # To do db stuff as dev use `sudo su dev`.
  config.vm.provision "shell-add-dev-user", type: "shell", inline: <<-SHELL
    adduser dev --disabled-login
    usermod -aG sudo dev
    echo "127.0.0.1 external-puzzle-massive" >> /etc/hosts

    sed --in-place "s/^PasswordAuthentication yes$/PasswordAuthentication no/" /etc/ssh/sshd_config
    sed --in-place "s/^#PasswordAuthentication yes$/PasswordAuthentication no/" /etc/ssh/sshd_config
    systemctl reload sshd
  SHELL

  config.vm.provision "setup", type: "shell", path: "bin/setup.sh"

  # The devsync.sh uses local-puzzle-massive when syncing files
  # Install the watchit command that is used in _infra/local/watchit.sh script.
  config.vm.provision "shell-watchit-support", type: "shell", inline: <<-SHELL
    echo "127.0.0.1 local-puzzle-massive" >> /etc/hosts
    pip install watchit
  SHELL

  config.vm.provision "shell-vagrant-local-ssh", privileged: false, type: "shell", inline: <<-SHELL
    ssh-keyscan -H local-puzzle-massive >> /home/vagrant/.ssh/known_hosts
    ssh-keygen -t rsa -C "vagrant@local-puzzle-massive" -N "" -q -f /home/vagrant/.ssh/id_rsa
  SHELL

  config.vm.provision "shell-vagrant-npm-install-and-build", privileged: false, type: "shell", inline: <<-SHELL
    cd /home/vagrant/puzzle-massive
    npm install
    npm run debug
  SHELL

  config.vm.provision "shell-dev-ssh", type: "shell", inline: <<-SHELL
    mkdir /home/dev/.ssh
    chown dev:dev /home/dev/.ssh
    chmod 700 /home/dev/.ssh
    cat /home/vagrant/.ssh/id_rsa.pub >> /home/dev/.ssh/authorized_keys
    chmod 600 /home/dev/.ssh/authorized_keys
    chown dev:dev /home/dev/.ssh/authorized_keys

    mkdir -p /usr/local/src/puzzle-massive;
    chown dev:dev /usr/local/src/puzzle-massive;
  SHELL

  config.vm.provision "shell-vagrant-devsync", privileged: false, type: "shell", inline: <<-SHELL
    cd /home/vagrant/puzzle-massive
    ./bin/devsync.sh
  SHELL

  config.vm.provision "shell-services-watchit-devsync", type: "shell", inline: <<-SHELL
    /home/vagrant/puzzle-massive/_infra/local/local-puzzle-massive-watchit.service.sh vagrant > /etc/systemd/system/local-puzzle-massive-watchit.service
    systemctl start local-puzzle-massive-watchit
    systemctl enable local-puzzle-massive-watchit

    /home/vagrant/puzzle-massive/_infra/local/local-puzzle-massive-auto-devsync.service.sh vagrant > /etc/systemd/system/local-puzzle-massive-auto-devsync.service
    systemctl start local-puzzle-massive-auto-devsync
    systemctl enable local-puzzle-massive-auto-devsync
  SHELL

  config.vm.provision "shell-init-dev-local", type: "shell", run: "never", inline: <<-SHELL
    cd /usr/local/src/puzzle-massive;
    sudo su --command '
      python -m venv .;
      make;
    ' dev
    make install;
    ./bin/appctl.sh stop -f;
    sudo su --command '
      ./bin/python api/api/create_database.py site.cfg;
      ./bin/python api/api/jobs/insert-or-replace-bit-icons.py;
      ./bin/python api/api/update_enabled_puzzle_features.py;
    ' dev
    nginx -t;
    systemctl reload nginx;
    ./bin/appctl.sh start;
    ./bin/appctl.sh status;
  SHELL

  config.vm.provision "shell-testdata-puzzles-quick", type: "shell", run: "never", inline: <<-SHELL
    cd /usr/local/src/puzzle-massive;
    sudo su --command '
      ./bin/puzzle-massive-testdata players --count=100;
      ./bin/puzzle-massive-testdata puzzles --count=10 --pieces=20 --size=800x800\!;
      ./bin/puzzle-massive-testdata puzzles --count=1 --pieces=100 --size=1800x800\!;
      ./bin/puzzle-massive-testdata puzzles --count=1 --pieces=100 --size=1800x1800\!;
      ./bin/puzzle-massive-testdata puzzles --count=1 --pieces=100 --size=800x1800\!;
      ./bin/puzzle-massive-testdata puzzles --count=1 --pieces=900 --size=6720x4480\!;
    ' dev
  SHELL

  config.vm.provision "shell-testdata-puzzles", type: "shell", run: "never", inline: <<-SHELL
    cd /usr/local/src/puzzle-massive;
    sudo su --command '
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

  # TODO: add systemctl service to run devsync.sh command when files change in
  # /home/vagrant/puzzle-massive/*

  # Run the bin/setup.sh script after logging in
end

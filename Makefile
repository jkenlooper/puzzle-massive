MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := all
.DELETE_ON_ERROR:
.SUFFIXES:

mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
project_dir := $(dir $(mkfile_path))

# Local pip is used by creating virtualenv and running `source ./bin/activate`

# Set to tmp/ when debugging the install
# make PREFIXDIR=${PWD}/tmp inspect.SRVDIR
# make PREFIXDIR=${PWD}/tmp ENVIRONMENT=development install
PREFIXDIR :=

# Set to development or production
ENVIRONMENT := development

ENV_FILE := ${PWD}/.env
PORTREGISTRY := ${PWD}/port-registry.cfg
SRVDIR := $(PREFIXDIR)/srv/puzzle-massive/
NGINXDIR := $(PREFIXDIR)/etc/nginx/
SYSTEMDDIR := $(PREFIXDIR)/etc/systemd/system/
DATABASEDIR := $(PREFIXDIR)/var/lib/puzzle-massive/sqlite3/
NGINXLOGDIR := $(PREFIXDIR)/var/log/nginx/puzzle-massive/
AWSTATSLOGDIR := $(PREFIXDIR)/var/log/awstats/puzzle-massive/
ARCHIVEDIR := $(PREFIXDIR)/var/lib/puzzle-massive/archive/
CACHEDIR := $(PREFIXDIR)/var/lib/puzzle-massive/cache/
PURGEURLLIST := $(PREFIXDIR)/var/lib/puzzle-massive/nginx/urls-to-purge.txt

# Set the internal ip which is used to secure access to admin/ pages.
INTERNALIP := $(shell hostname -I | cut -d' ' -f1)

# Get the version from the package.json
TAG := $(shell cat package.json | python -c 'import sys, json; print(json.load(sys.stdin)["version"])')

# For debugging what is set in variables
inspect.%:
	@echo $($*)

ifeq ($(shell which virtualenv),)
$(error run "./bin/setup.sh" to install virtualenv)
endif
ifeq ($(shell ls bin/activate),)
$(error run "virtualenv . -p python3")
endif
ifneq ($(shell which pip),$(project_dir)bin/pip)
$(warning run "source bin/activate" to activate the virtualenv. Using $(shell which pip). Ignore this warning if using sudo make install.)
endif

# Always run.  Useful when target is like targetname.% .
# Use $* to get the stem
FORCE:

objects := site.cfg web/puzzle-massive.conf web/puzzle-massive--down.conf stats/awstats.puzzle.massive.xyz.conf stats/awstats-puzzle-massive-crontab


#####

#web/dhparam.pem:
	#openssl dhparam -out $@ 2048

bin/chill: chill/requirements.txt requirements.txt
	pip install --upgrade --upgrade-strategy eager -r $<
	touch $@;

objects += chill/puzzle-massive-chill.service
chill/puzzle-massive-chill.service: chill/puzzle-massive-chill.service.sh
	./$< $(ENVIRONMENT) $(project_dir) > $@

# Create a tar of the frozen directory to prevent manually updating files within it.
# Not using a frozen.tar.gz for now.
#objects += frozen.tar.gz
frozen.tar.gz: db.dump.sql site.cfg package.json $(shell find templates/ -type f -print) $(shell find documents/ -type f -print) $(shell find queries/ -type f -print)
	bin/freeze.sh $@

objects += db.dump.sql
# Create db.dump.sql from chill-data.sql and any chill-*.yaml files
db.dump.sql: site.cfg chill-data.sql $(wildcard chill-*.yaml)
	bin/create-db-dump-sql.sh

# Also installs janitor, scheduler and artist
bin/puzzle-massive-api: api/requirements.txt requirements.txt api/setup.py
	pip install --upgrade --upgrade-strategy eager -r $<
	touch $@;

bin/puzzle-massive-divulger: divulger/requirements.txt requirements.txt divulger/setup.py
	pip install --upgrade --upgrade-strategy eager -r $<
	touch $@;


objects += api/puzzle-massive-api.service
api/puzzle-massive-api.service: api/puzzle-massive-api.service.sh
	./$< $(ENVIRONMENT) $(project_dir) > $@

objects += api/puzzle-massive-artist.service
api/puzzle-massive-artist.service: api/puzzle-massive-artist.service.sh
	./$< $(project_dir) > $@

objects += api/puzzle-massive-janitor.service
api/puzzle-massive-janitor.service: api/puzzle-massive-janitor.service.sh
	./$< $(project_dir) > $@

objects += api/puzzle-massive-scheduler.service
api/puzzle-massive-scheduler.service: api/puzzle-massive-scheduler.service.sh
	./$< $(project_dir) > $@

objects += divulger/puzzle-massive-divulger.service
divulger/puzzle-massive-divulger.service: divulger/puzzle-massive-divulger.service.sh
	./$< $(project_dir) > $@

objects += api/puzzle-massive-cache-purge.path
api/puzzle-massive-cache-purge.path: api/puzzle-massive-cache-purge.path.sh
	./$< $(PURGEURLLIST) > $@
objects += api/puzzle-massive-cache-purge.service
api/puzzle-massive-cache-purge.service: api/puzzle-massive-cache-purge.service.sh
	./$< $(PORTREGISTRY) $(CACHEDIR) $(project_dir) $(PURGEURLLIST) > $@

objects += api/puzzle-massive-backup-db.service
api/puzzle-massive-backup-db.service: api/puzzle-massive-backup-db.service.sh
	./$< $(ENVIRONMENT) $(project_dir) > $@
objects += api/puzzle-massive-backup-db.timer
api/puzzle-massive-backup-db.timer: api/puzzle-massive-backup-db.timer.sh
	./$< $(ENVIRONMENT) > $@

site.cfg: site.cfg.sh $(PORTREGISTRY) $(ENV_FILE)
	./$< $(ENVIRONMENT) $(SRVDIR) $(DATABASEDIR) $(PORTREGISTRY) $(ARCHIVEDIR) $(CACHEDIR) $(PURGEURLLIST) > $@

web/puzzle-massive.conf: web/puzzle-massive.conf.sh $(PORTREGISTRY)
	./$< $(ENVIRONMENT) $(SRVDIR) $(NGINXLOGDIR) $(PORTREGISTRY) $(INTERNALIP) $(CACHEDIR) > $@
web/puzzle-massive--down.conf: web/puzzle-massive--down.conf.sh $(PORTREGISTRY)
	./$< $(ENVIRONMENT) $(SRVDIR) $(NGINXLOGDIR) $(PORTREGISTRY) $(INTERNALIP) $(CACHEDIR) > $@

#ifeq ($(ENVIRONMENT),production)
## Only create the dhparam.pem if needed.
#objects += web/dhparam.pem
#web/puzzle-massive.conf: web/dhparam.pem
#endif

stats/awstats.puzzle.massive.xyz.conf: stats/awstats.puzzle.massive.xyz.conf.sh
	./$< $(NGINXLOGDIR) > $@

stats/awstats-puzzle-massive-crontab: stats/awstats-puzzle-massive-crontab.sh
	./$< $(SRVDIR) $(AWSTATSLOGDIR) > $@

.PHONY: puzzle-massive-$(TAG).tar.gz
puzzle-massive-$(TAG).tar.gz: bin/dist.sh
	./$< $(abspath $@)

######

.PHONY: all
all: bin/chill bin/puzzle-massive-api bin/puzzle-massive-divulger $(objects)

.PHONY: install
install:
	./bin/install.sh $(ENVIRONMENT) $(SRVDIR) $(NGINXDIR) $(NGINXLOGDIR) $(AWSTATSLOGDIR) $(SYSTEMDDIR) $(DATABASEDIR) $(ARCHIVEDIR) $(CACHEDIR) $(PURGEURLLIST)

# Remove any created files in the src directory which were created by the
# `make all` recipe.
.PHONY: clean
clean:
	rm $(objects)
	pip uninstall --yes -r chill/requirements.txt
	pip uninstall --yes -r api/requirements.txt
	pip uninstall --yes -r divulger/requirements.txt

# Remove files placed outside of src directory and uninstall app.
# Will also remove the sqlite database file.
.PHONY: uninstall
uninstall:
	./bin/uninstall.sh $(SRVDIR) $(NGINXDIR) $(SYSTEMDDIR) $(DATABASEDIR) $(ARCHIVEDIR) $(CACHEDIR) $(PURGEURLLIST)

.PHONY: dist
dist: puzzle-massive-$(TAG).tar.gz

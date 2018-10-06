#!/usr/bin/env bash

set -eu -o pipefail

SRVDIR=$1
AWSTATSLOGDIR=$2

cat <<HERE
# m h	dom mon dow user	command
26 *	* * * root perl /usr/share/awstats/tools/awstats_buildstaticpages.pl -awstatsprog=/usr/lib/cgi-bin/awstats.pl -config=puzzle.massive.xyz -update -dir=${SRVDIR}stats/ > ${AWSTATSLOGDIR}build.log 2> ${AWSTATSLOGDIR}error.log
# An empty line is required at the end of this file for a valid cron file.
HERE

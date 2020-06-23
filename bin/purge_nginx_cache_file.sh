#!/usr/bin/env bash

# The cache_url is where the cache server found it on the origin server.
# For example:
# /theme/2.3.2/icons.svg
# Set cache_url_list to a text file with each line being a cache_url to purge.
cache_url_list=$1

# http://localhost:6301
origin_server=$2

# nginx cache dir
nginx_cache_dir=$3

# Thanks to https://serverfault.com/questions/493411/how-to-delete-single-nginx-cache-file/992173
# When proxy_cache_path has parameters levels=1:2 and use_temp_path=off
function nxcacheof {
    local x;
    x=$(echo -n "$1" | md5sum)
    echo "${x:31:1}/${x:29:2}/${x:0:32}"
}

function purge_cache_url_list {
    if test -f "${cache_url_list}"; then
        tmp_cache_url_list=$(mktemp)

        # copy the url list to the tmp/ directory before removing it
        cp "${cache_url_list}" "${tmp_cache_url_list}"
        rm -f "${cache_url_list}";

        # Process the cache url list
        while read cache_url; do
            echo ${origin_server}${cache_url};
            rm -f "${nginx_cache_dir}$(nxcacheof ${origin_server}${cache_url})";
        done < "${tmp_cache_url_list}";
        rm -f "${tmp_cache_url_list}";
    fi;
}

purge_cache_url_list;
# Double check by delaying a second and running again.
sleep 1;
purge_cache_url_list;

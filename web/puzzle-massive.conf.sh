#!/usr/bin/env bash

set -eu -o pipefail

ENVIRONMENT=$1
SRVDIR=$2
NGINXLOGDIR=$3
NGINXDIR=$4
PORTREGISTRY=$5
INTERNALIP=$6
CACHEDIR=$7
STATE=$8

# shellcheck source=/dev/null
source "$PORTREGISTRY"

# shellcheck source=/dev/null
source .env

DATE=$(date)

DEBUG=$(./bin/site-cfg.py site.cfg DEBUG || echo 'False')

# Load snippet confs
file_ssl_params_conf=$(cat web/ssl_params.conf)
file_error_page_conf=$(cat web/error_page.conf)

function ssl_certs {
  if test "${ENVIRONMENT}" == 'development'; then

    if test -e .has-certs; then
    cat <<HEREENABLESSLCERTS
      # certs created for local development
      ssl_certificate "${NGINXDIR}ssl/local-puzzle-massive.crt";
      ssl_certificate_key "${NGINXDIR}ssl/local-puzzle-massive.key";
HEREENABLESSLCERTS
    else
    cat <<HERETODOSSLCERTS
      # certs for local development can be created by running './bin/provision-local-ssl-certs.sh'
      # uncomment after they exist (run make again)
      #ssl_certificate "${NGINXDIR}ssl/local-puzzle-massive.crt";
      #ssl_certificate_key "${NGINXDIR}ssl/local-puzzle-massive.key";
HERETODOSSLCERTS
    fi

  else

    if test -e .has-certs; then
    cat <<HEREENABLESSLCERTS
      # certs created from certbot
      ssl_certificate /etc/letsencrypt/live/puzzle.massive.xyz/fullchain.pem;
      ssl_certificate_key /etc/letsencrypt/live/puzzle.massive.xyz/privkey.pem;
HEREENABLESSLCERTS
    else
    cat <<HERETODOSSLCERTS
      # certs can be created from running 'bin/provision-certbot.sh ${SRVDIR}'
      # TODO: uncomment after they exist
      #ssl_certificate /etc/letsencrypt/live/puzzle.massive.xyz/fullchain.pem;
      #ssl_certificate_key /etc/letsencrypt/live/puzzle.massive.xyz/privkey.pem;
HERETODOSSLCERTS
    fi
  fi

  if (test -f web/dhparam.pem); then
  cat <<HERE
    ## Danger Zone.  Only uncomment if you know what you are doing.
    #ssl_dhparam /etc/nginx/ssl/dhparam.pem;
HERE
  fi
}

function server_header {
  cat <<HERE
  listen 80;
  server_tokens off;
HERE
  #if test "${ENVIRONMENT}" == 'development'; then
  #else
  #fi

  if test -e .has-certs; then
    cat <<HEREBECERTS
    listen 443 ssl http2;
    ${file_ssl_params_conf}
HEREBECERTS
    ssl_certs;
  else
    cat <<HERENOCERTS
    # Site is not configured for ssl certs. No .has-certs file found.
    #listen 443 ssl http2;
HERENOCERTS
    # ssl_certs function will comment out the ssl_certificate directive
    ssl_certs;
  fi
}

cat <<HERE
# File generated from $0
# on ${DATE}

limit_conn_zone \$binary_remote_addr zone=addr:1m;
limit_req_zone \$binary_remote_addr zone=piece_move_limit_per_ip:1m rate=60r/m;
limit_req_zone \$binary_remote_addr zone=piece_token_limit_per_ip:1m rate=60r/m;
limit_req_zone \$binary_remote_addr zone=puzzle_upload_limit_per_ip:1m rate=3r/m;
limit_req_zone \$server_name zone=puzzle_upload_limit_per_server:1m rate=20r/m;
limit_req_zone \$binary_remote_addr zone=puzzle_list_limit_per_ip:1m rate=30r/m;
limit_req_zone \$server_name zone=puzzle_list_limit_per_server:1m rate=20r/s;
limit_req_zone \$binary_remote_addr zone=player_email_register_limit_per_ip:1m rate=1r/m;

limit_req_zone \$binary_remote_addr zone=chill_puzzle_limit_per_ip:1m rate=30r/m;
limit_req_zone \$binary_remote_addr zone=chill_site_internal_limit_per_ip:1m rate=10r/s;
# 10 requests a second = 100ms
limit_req_zone \$server_name zone=chill_site_internal_limit:1m rate=10r/s;

proxy_headers_hash_bucket_size 2048;

HERE

if test "${STATE}" == 'up'; then
cat <<HEREBEUP
map \$request_uri \$cache_expire {
  default off;
HEREBEUP
if test "${DEBUG}" = 'True'; then
cat <<HEREBEUPDEBUG
  # DEBUG=True means that cache on /chill/site/* is off.
  ~/chill/site/.* -1;
  ~/theme/.*?/.* -1;
  # Any below matches for chill/site/ and theme/ are ignored.
HEREBEUPDEBUG
fi
cat <<HEREBEUP
  ~/chill/site/internal/player-bit/.* 1d;
  ~/chill/site/internal/attribution/.* 1d;
  ~/chill/site/claim-player/.* off;
  ~/chill/site/reset-login/.* off;
  ~/chill/site/bit-icons/.* 1y;
  ~/chill/site/puzzle/.* off;
  ~/chill/site/front/.* 1m;
  ~/chill/site/api/.* 1m;
  ~/chill/site/puzzle-list/.* 60m;
  ~/chill/site/high-scores/ 60m;
  ~/chill/site/admin/.* off;
  ~/chill/site/.* 1d;
  ~/theme/.*?/.* 1y;
  ~/media/.* 1M;
  ~/resources/.* 1M;
  ~/.*?.png 1M;
  /favicon.ico 1M;
  /humans.txt 1d;
  /robots.txt 1d;
  /site.webmanifest 1d;
  /.well-known/.* off;
  /newapi/gallery-puzzle-list/ 1m;
  /newapi/puzzle-list/ 1m;
  # Safeguard for no cache on player-puzzle-list
  /newapi/player-puzzle-list/ off;
}

# Manually purge files in cache with the script ./bin/purge_nginx_cache_file.sh
proxy_cache_path ${CACHEDIR} levels=1:2 keys_zone=pm_cache_zone:10m inactive=600m use_temp_path=off;

HEREBEUP

else
# STATE is down

cat <<HEREBEDOWN
HEREBEDOWN

fi
# end STATE


cat <<HERE
map \$request_uri \$hotlinking_policy {
  # Set routes to 0 to allow hotlinking or direct loading (bookmarked).

  # anonymous login links
  ~/puzzle-api/bit/.* 0;
  ~/newapi/user-login/.* 0;

  # Pages on the site.
  / 0;
  ~/.+/$ 0;

  # og:image image that can be used when sharing links
  /puzzle-massive-logo-600.png 0;
  ~/resources/.*/preview_full.jpg 0;

  # files in root
  /favicon.ico 0;
  /humans.txt 0;
  /robots.txt 0;

  # certbot challenges
  ~/.well-known/.* 0;

  default \$invalid_referer;
}

map \$request_uri \$loggable {
    # Don't log requests to the anonymous login link.
    ~/puzzle-api/bit/.* 0;
    ~/newapi/user-login/.* 0;

    default 1;
}


# Redirect for old hosts
server {
  listen       80;
  server_tokens off;
  server_name puzzle.weboftomorrow.com www.puzzle.massive.xyz;
  return       301 http://puzzle.massive.xyz\$request_uri;
}
HERE


cat <<HERECACHESERVER
# Cache server
server {
HERECACHESERVER

server_header;

if test "${ENVIRONMENT}" == 'development'; then
cat <<HEREBEDEVELOPMENT
  # Only when in development should the site be accessible via internal ip.
  # This makes it easier to test with other devices that may not be able to
  # update a /etc/hosts file.
  server_name local-puzzle-massive $INTERNALIP;
HEREBEDEVELOPMENT
else
cat <<HEREBEPRODUCTION
  # Generated docs use puzzle-massive-blue puzzle-massive-green.
  # Use of puzzle-blue and puzzle-green is deprecated.
  server_name puzzle-massive-blue puzzle-blue puzzle-massive-green puzzle-green ${DOMAIN_NAME};

HEREBEPRODUCTION
fi
cat <<HERECACHESERVER

  add_header X-Frame-Options DENY;
  add_header X-Content-Type-Options nosniff;

  root ${SRVDIR}root;

  access_log  ${NGINXLOGDIR}access.log;
  error_log   ${NGINXLOGDIR}error.log;

  # The hotlinking_policy uses this with the invalid_referer variable.
  valid_referers server_names;

  # Limit the max simultaneous connections per ip address (10 per browser * 4 if within LAN)
  # Skip doing this so players on a shared VPN are not blocked.
  #limit_conn   addr 40;

  # Prevent POST upload sizes that are larger than this.
  client_max_body_size  20m;

  # The value none enables keep-alive connections with all browsers.
  keepalive_disable  none;

  # Rewrite the homepage url
  rewrite ^/index.html\$ / permanent;

  # redirect the old puzzlepage url
  rewrite ^/puzzle/(.*)\$ /chill/site/puzzle/\$1/ permanent;

  # rewrite old bit login (Will probably always need to have this rewritten)
  rewrite ^/puzzle-api/bit/([^/]+)/?\$ /newapi/user-login/\$1/;

  # handle old style of scale query param where 'scale=' meant to use without scaling
  rewrite ^/chill/site/puzzle/([^/]+)/\$ /chill/site/puzzle/\$1/scale/0/? redirect;

  # redirect old puzzle queues
  rewrite ^/chill/site/queue/(.*)\$ /chill/site/puzzle-list/ permanent;

  # temporary redirect player profile page
  rewrite ^/chill/site/player/[^/]+/\$ /chill/site/player/ redirect;

  # Temporary redirect document pages to allow robots to index them.
  rewrite ^/chill/site/(about|faq|help|credits|buy-stuff)/\$ /\$1/ redirect;

  # Home page goes to the chill/site/front/
  rewrite ^/\$ /chill/site/front/ last;

  # Document pages go to /chill/site/
  rewrite ^/d/(.*)/\$ /chill/site/\$1/ last;

  # redirect old document pages
  rewrite ^/(about|faq|help|credits|buy-stuff)/\$ /d/\$1/ redirect;

  # Ignore query params on media so they are not part of the cache.
  rewrite ^/(media/.*)\$ /\$1? last;

  # Keep the query params on /resources/.*; they are for cache-busting.
  #rewrite ^/(resources/.*)\$ /\$1? last;

  # Ignore query params on root files so they are not part of the cache.
  # Matches root files: /humans.txt, /robots.txt, /puzzle-massive-logo-600.png
  rewrite ^/([^/]+)(\.txt|\.png)\$ /\$1\$2? last;

HERECACHESERVER
if test "${ENVIRONMENT}" != 'development'; then
cat <<HERECACHESERVERPRODUCTION
  # Ignore query params on theme for production so they are not part of the cache.
  rewrite ^/(theme/.*)\$ /\$1? last;

  # Ignore query params on favicon.ico for production.
  rewrite ^/(favicon\.ico)\$ /\$1? last;

  # Ignore query params on site.webmanifest for production.
  rewrite ^/(site.webmanifest)\$ /\$1? last;
HERECACHESERVERPRODUCTION
fi

if test "${STATE}" == 'up'; then
cat <<HERECACHESERVERUP
  location / {
    if (\$hotlinking_policy) {
      return 444;
    }

    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$remote_addr;
    proxy_set_header X-Forwarded-Host \$remote_addr;
    proxy_cache pm_cache_zone;
    add_header X-Proxy-Cache \$upstream_cache_status;
    include proxy_params;
    proxy_pass http://localhost:${PORTORIGIN};
  }

  location ~* ^/chill/site/puzzle/(.*/)?$ {
    # At this time all routes on chill/* are GETs
    limit_except GET {
      deny all;
    }

    # Redirect players without a user or shareduser cookie to the new-player page
    if (\$http_cookie !~* "(user|shareduser)=([^;]+)(?:;|\$)") {
      rewrite ^/chill/(.*)\$  /chill/site/new-player/?next=/chill/\$1? redirect;
    }

    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$remote_addr;
    proxy_set_header X-Forwarded-Host \$remote_addr;
    proxy_cache pm_cache_zone;
    add_header X-Proxy-Cache \$upstream_cache_status;
    include proxy_params;
    proxy_pass http://localhost:${PORTORIGIN};
  }

  location = /chill/site/new-player/ {
    # At this time all routes on chill/* are GETs
    limit_except GET {
      deny all;
    }
    # Redirect players with a user cookie to the player profile page
    if (\$http_cookie ~* "user=([^;]+)(?:;|\$)") {
      rewrite ^/chill/(.*)\$  /chill/site/player/ redirect;
    }

    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$remote_addr;
    proxy_set_header X-Forwarded-Host \$remote_addr;
    proxy_cache pm_cache_zone;
    add_header X-Proxy-Cache \$upstream_cache_status;
    include proxy_params;
    proxy_pass http://localhost:${PORTORIGIN};
  }

  # Skipping divulger since it is not needed at the moment.
  #location /divulge/ {
  #  proxy_pass_header Server;
  #  proxy_set_header X-Real-IP  \$remote_addr;
  #  proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
  #  proxy_pass http://localhost:${PORTDIVULGER};

  #  # Upgrade to support websockets
  #  proxy_http_version 1.1;
  #  proxy_set_header Upgrade \$http_upgrade;
  #  proxy_set_header Connection "upgrade";

  #  # Default timeout is 60s
  #  proxy_read_timeout 500s;
  #}

  # /stream/puzzle/<channel>/
  location ~* ^/stream/puzzle/([^/]+)/\$ {
    if (\$hotlinking_policy) {
      return 444;
    }
    proxy_pass_header Server;
    proxy_set_header  X-Real-IP  \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_set_header Host \$http_host;
    proxy_redirect off;

    # Set timeout for connections to be 5 minutes
    proxy_read_timeout 300s;

    # Required in order to WebSockets or Streaming (sse). Async workers are
    # needed then.
    proxy_buffering off;

    proxy_pass http://localhost:${PORTSTREAM};

    # Channel is in the route, so /stream/puzzle/puzzle_id/ will go to: /stream?channel=puzzle:puzzle_id
    rewrite ^/stream/puzzle/([^/]+)/\$ /stream?channel=puzzle:\$1? break;
  }

HERECACHESERVERUP
else
cat <<HERECACHESERVERDOWN
  location / {
    if (\$hotlinking_policy) {
      return 444;
    }
    try_files \$uri \$uri =404;
  }
  location /media/ {
    if (\$hotlinking_policy) {
      return 444;
    }
    root ${SRVDIR};
    try_files \$uri \$uri =404;
  }

  location = / {
    rewrite ^/.* /error.html break;
  }
  location /chill/site/ {
    # stop caching
    expires -1;
    add_header Cache-Control "public";

    rewrite ^/.* /error.html break;
  }
  location /newapi/ {
    return 503;
  }


HERECACHESERVERDOWN
fi

cat <<HERECACHESERVER

  location = /newapi/message/ {
    limit_except GET {
      deny all;
    }
    # stop caching
    expires -1;
    add_header Cache-Control "public";
    # Allow this content to be loaded in the error page iframe
    add_header X-Frame-Options ALLOW;
    rewrite ^/.* /puzzle-massive-message.html break;
  }

  ${file_error_page_conf}

  }
HERECACHESERVER


if test "${STATE}" == 'up'; then
cat <<HEREORIGINSERVER
# Origin server
server {
  server_name localhost;
  listen      ${PORTORIGIN};

  set_real_ip_from localhost;
  real_ip_header X-Real-IP;
  real_ip_recursive on;

  root ${SRVDIR}root;

  access_log  ${NGINXLOGDIR}access.log combined if=\$loggable;
  error_log   ${NGINXLOGDIR}error.log;

  # Serve any static files at ${SRVDIR}root/*
  location / {
    expires \$cache_expire;
    add_header Cache-Control "public";
    try_files \$uri \$uri =404;
  }

  location /stats/ {
    root   ${SRVDIR}stats;
    index  awstats.puzzle.massive.xyz.html;
    auth_basic            "Restricted";
    auth_basic_user_file  ${SRVDIR}.htpasswd;
    access_log ${NGINXLOGDIR}access.awstats.log;
    error_log ${NGINXLOGDIR}error.awstats.log;
    rewrite ^/stats/(.*)\$  /\$1 break;
  }

  location /newapi/ {
    proxy_pass_header Server;
    proxy_set_header  X-Real-IP  \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_pass http://localhost:${PORTAPI};
    proxy_redirect http://localhost:${PORTAPI}/ http://\$host/;

    rewrite ^/newapi/(.*)\$ /\$1 break;
  }

  location /newapi/puzzle-upload/ {
    # Prevent too many uploads at once
    limit_req zone=puzzle_upload_limit_per_ip burst=5 nodelay;
    limit_req zone=puzzle_upload_limit_per_server burst=20 nodelay;

    proxy_pass_header Server;
    proxy_set_header  X-Real-IP  \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_redirect http://localhost:${PORTAPI}/ http://\$host/;
    proxy_pass http://localhost:${PORTAPI};
    rewrite ^/newapi/(.*)\$ /\$1 break;
  }

  location /newapi/player-email-register/ {
    # Prevent too many requests at once
    limit_req zone=player_email_register_limit_per_ip burst=5 nodelay;

    proxy_pass_header Server;
    proxy_set_header  X-Real-IP  \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_redirect http://localhost:${PORTAPI}/ http://\$host/;
    proxy_pass http://localhost:${PORTAPI};
    rewrite ^/newapi/(.*)\$ /\$1 break;
  }

  location /newapi/gallery-puzzle-list/ {
    expires \$cache_expire;
    add_header Cache-Control "public";

    proxy_pass_header Server;
    proxy_set_header  X-Real-IP  \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_redirect http://localhost:${PORTAPI}/ http://\$host/;
    proxy_pass http://localhost:${PORTAPI};
    rewrite ^/newapi/(.*)\$ /\$1 break;
  }

  location /newapi/puzzle-list/ {
    expires \$cache_expire;
    add_header Cache-Control "public";

    # Prevent too many puzzle list queries at once.
    limit_req zone=puzzle_list_limit_per_ip burst=20 nodelay;
    limit_req zone=puzzle_list_limit_per_server burst=200;
    limit_req_status 429;

    proxy_pass_header Server;
    proxy_set_header  X-Real-IP  \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_redirect http://localhost:${PORTAPI}/ http://\$host/;
    proxy_pass http://localhost:${PORTAPI};
    rewrite ^/newapi/(.*)\$ /\$1 break;
  }

  location /newapi/admin/ {
HEREORIGINSERVER
if test "${ENVIRONMENT}" != 'development'; then
cat <<HEREORIGINSERVERPRODUCTION
    # Set to droplet ip not floating ip.
    # Requires using SOCKS proxy (ssh -D 8080 user@host)
    allow $INTERNALIP;
    allow 127.0.0.1;
    deny all;
HEREORIGINSERVERPRODUCTION
fi
cat <<HEREORIGINSERVER
    auth_basic "Restricted Content";
    auth_basic_user_file ${SRVDIR}.htpasswd;

    proxy_pass_header Server;
    proxy_set_header  X-Real-IP  \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_pass http://localhost:${PORTAPI};
    proxy_redirect http://localhost:${PORTAPI}/ http://\$host/;
    rewrite ^/newapi/(.*)\$ /\$1 break;
  }

  location ~* ^/newapi/puzzle/.*/piece/.*/token/ {
    # TODO: not sure why keepalive_timeout was set to 0 before.
    #keepalive_timeout 0;
    limit_req zone=piece_token_limit_per_ip burst=60 nodelay;
    limit_req_status 429;

    proxy_pass_header Server;
    proxy_set_header  X-Real-IP  \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_redirect http://localhost:${PORTAPI}/ http://\$host/;
    proxy_pass http://localhost:${PORTAPI};
    rewrite ^/newapi/(.*)\$ /\$1 break;
  }

  location ~* ^/newapi/puzzle/.*/piece/.*/move/ {
    # Limit to max of 4 simultaneous puzzle piece moves per ip addr
    #limit_conn   addr 4;
    # Not exactly sure why, but setting it to 4 will not allow more then 3 players on a single IP.
    # This is set to 40 to allow at most 39 players on one IP
    limit_conn   addr 40;

    # TODO: not sure why keepalive_timeout was set to 0 before.
    #keepalive_timeout 0;
    limit_req zone=piece_move_limit_per_ip burst=60 nodelay;
    limit_req_status 429;

    proxy_pass_header Server;
    proxy_set_header  X-Real-IP  \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_redirect http://localhost:${PORTAPI}/ http://\$host/;
    proxy_pass http://localhost:${PORTAPI};
    rewrite ^/newapi/(.*)\$ /\$1 break;
  }

  location ~* ^/chill/site/puzzle/.*\$ {
    expires \$cache_expire;

    # Allow loading up to 15 puzzles with each request being delayed by
    # 2 seconds.
    limit_req zone=chill_puzzle_limit_per_ip burst=15;

    proxy_pass_header Server;
    proxy_set_header  X-Real-IP  \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_redirect http://localhost:${PORTCHILL}/ http://\$host/;

    proxy_pass http://localhost:${PORTCHILL};

    rewrite ^/chill/(.*)\$  /\$1 break;
  }

  location /chill/site/internal/ {
    # Limit the response rate for the server as these requests can be called
    # multiple times on a page request.
    # Each request is delayed by 100ms up to 20 seconds.
    limit_req zone=chill_site_internal_limit_per_ip burst=10 nodelay;
    limit_req zone=chill_site_internal_limit burst=200;
    limit_req_status 429;

    proxy_pass_header Server;
    proxy_set_header  X-Real-IP  \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_redirect http://localhost:${PORTCHILL}/ http://\$host/;

    proxy_pass http://localhost:${PORTCHILL};

    expires \$cache_expire;
    add_header Cache-Control "public";
    rewrite ^/chill/(.*)\$  /\$1 break;
  }


  location /chill/ {
    # Location for /chill/theme/* /chill/media/* and others
    # Note that in development the /chill/theme/ and /chill/media/ are used, but
    # in production they argghhhhgghhhihfhghffhgghh.
    proxy_pass_header Server;
    proxy_set_header  X-Real-IP  \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    expires \$cache_expire;
    add_header Cache-Control "public";
    proxy_redirect http://localhost:${PORTCHILL}/ http://\$host/;

    proxy_pass http://localhost:${PORTCHILL};
    rewrite ^/chill/(.*)\$  /\$1 break;
  }

  location /chill/site/ {
    proxy_pass_header Server;
    proxy_set_header  X-Real-IP  \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_redirect http://localhost:${PORTCHILL}/ http://\$host/;

    expires \$cache_expire;
    add_header Cache-Control "public";

    proxy_pass http://localhost:${PORTCHILL};

    rewrite ^/chill/(.*)\$  /\$1 break;
  }

  location = /chill/site/new-player/ {
    proxy_pass_header Server;
    proxy_set_header  X-Real-IP  \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_redirect http://localhost:${PORTCHILL}/ http://\$host/;

    expires \$cache_expire;
    add_header Cache-Control "public";

    proxy_pass http://localhost:${PORTCHILL};

    rewrite ^/chill/(.*)\$  /\$1 break;
  }

  location /chill/site/admin/ {

HEREORIGINSERVER
if test "${ENVIRONMENT}" != 'development'; then
cat <<HEREORIGINSERVERPRODUCTION
    # Set to droplet ip not floating ip.
    # Requires using SOCKS proxy (ssh -D 8080 user@host)
    allow $INTERNALIP;
    allow 127.0.0.1;
    deny all;
HEREORIGINSERVERPRODUCTION
fi
cat <<HEREORIGINSERVER

    proxy_pass_header Server;
    proxy_set_header  X-Real-IP  \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_redirect http://localhost:${PORTCHILL}/ http://\$host/;

    proxy_pass http://localhost:${PORTCHILL};

    auth_basic "Restricted Content";
    auth_basic_user_file ${SRVDIR}.htpasswd;

    rewrite ^/chill/(.*)\$  /\$1 break;
  }

HEREORIGINSERVER
if test "${ENVIRONMENT}" != 'development'; then
cat <<HEREBEPRODUCTION
  location ~* ^/theme/.*?/(.*)\$ {
    expires \$cache_expire;
    add_header Cache-Control "public";
    alias ${SRVDIR}dist/\$1;
  }

  location /media/ {
    expires \$cache_expire;
    add_header Cache-Control "public";
    root ${SRVDIR};
    try_files \$uri \$uri =404;
  }
HEREBEPRODUCTION

else

cat <<HEREBEDEVELOPMENT
  location /theme/ {
    rewrite ^/theme/(.*)\$  /chill/theme/\$1;
  }

  location /media/ {
    rewrite ^/media/(.*)\$  /chill/media/\$1;
  }
HEREBEDEVELOPMENT
fi
cat <<HEREORIGINSERVER

  location /media/bit-icons/ {
    expires \$cache_expire;
    add_header Cache-Control "public";
    root ${SRVDIR};
    try_files \$uri \$uri =404;
  }

  location ~* ^/resources/.*/(scale-100/raster.png|scale-100/raster.css|pzz.css|pieces.png)\$ {
    expires \$cache_expire;
    add_header Cache-Control "public";
    root ${SRVDIR};
    try_files \$uri \$uri =404;
  }
  location ~* ^/resources/.*/(preview_full.jpg)\$ {
    expires \$cache_expire;
    add_header Cache-Control "public";
    root ${SRVDIR};
    try_files \$uri \$uri =404;
  }
  location ~* ^/resources/.*/(original.jpg)\$ {
    allow $INTERNALIP;
    allow 127.0.0.1;
    deny all;
    root ${SRVDIR};
    try_files \$uri \$uri =404;
  }

  ${file_error_page_conf}

}
HEREORIGINSERVER
fi


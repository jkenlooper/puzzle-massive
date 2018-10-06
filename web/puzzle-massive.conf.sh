#!/usr/bin/env bash

set -eu -o pipefail

ENVIRONMENT=$1
SRVDIR=$2
NGINXLOGDIR=$3
PORTREGISTRY=$4

# shellcheck source=/dev/null
source "$PORTREGISTRY"

cat <<HERE

limit_conn_zone \$binary_remote_addr zone=addr:1m;
limit_req_zone \$binary_remote_addr zone=req_limit_per_ip:1m rate=8r/s;
limit_req_zone \$binary_remote_addr zone=piece_move_limit_per_ip:1m rate=60r/m;

server {
  # Redirect for old hosts
  listen       80;
  server_name puzzle.weboftomorrow.com www.puzzle.massive.xyz;
  return       301 http://puzzle.massive.xyz\$request_uri;
}

server {
  listen      80;
  #listen 443 ssl http2;

  ## SSL Params
  # from https://cipherli.st/
  # and https://raymii.org/s/tutorials/Strong_SSL_Security_On_nginx.html

  #ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
  #ssl_prefer_server_ciphers on;
  #ssl_ciphers "EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH";
  #ssl_ecdh_curve secp384r1;
  #ssl_session_cache shared:SSL:10m;
  #ssl_session_tickets off;
  #ssl_stapling on;
  #ssl_stapling_verify on;
  #resolver 8.8.8.8 8.8.4.4 valid=300s;
  #resolver_timeout 5s;
  ## Disable preloading HSTS for now.  You can use the commented out header line that includes
  ## the "preload" directive if you understand the implications.
  ##add_header Strict-Transport-Security "max-age=63072000; includeSubdomains; preload";
  #add_header Strict-Transport-Security "max-age=63072000; includeSubdomains";
  #add_header X-Frame-Options DENY;
  #add_header X-Content-Type-Options nosniff;

HERE
if (test -f web/dhparam.pem); then
cat <<HERE
  ssl_dhparam /etc/nginx/ssl/dhparam.pem;
HERE
fi
cat <<HERE


  root ${SRVDIR}root;

  access_log  ${NGINXLOGDIR}access.log;
  error_log   ${NGINXLOGDIR}error.log;

  location = /humans.txt {}
  location = /robots.txt {}
  location = /favicon.ico {}

  # Limit the max simultaneous connections per ip address (10 per browser * 4 if within LAN)
  limit_conn   addr 40;
  limit_req zone=req_limit_per_ip burst=10;

  client_max_body_size  20m;
  keepalive_disable  none;

  # Rewrite the homepage url
  rewrite ^/index.html\$ / permanent;
  rewrite ^/\$ /chill/site/front/ last;

  # redirect the old puzzlepage url
  rewrite ^/puzzle/(.*)\$ /chill/site/puzzle/\$1/ permanent;

  # rewrite old bit login (Will probably always need to have this rewritten)
  rewrite ^/puzzle-api/bit/([^/]+)/?\$ /newapi/user-login/\$1/;

  # handle old style of scale query param where 'scale=' meant to use without scaling
  rewrite ^/chill/site/puzzle/([^/]+)/\$ /chill/site/puzzle/\$1/scale/\$arg_scale/?;
  rewrite ^/chill/site/puzzle/([^/]+)/scale//\$ /chill/site/puzzle/\$1/scale/0/? last;
  rewrite ^/chill/site/puzzle/([^/]+)/scale/(\d+)/\$ /chill/site/puzzle/\$1/scale/1/? last;

  location /stats/ {
    root   ${SRVDIR}stats;
    index  awstats.puzzle.massive.xyz.html;
    #auth_basic            "Restricted";
    #auth_basic_user_file  ${SRVDIR}.htpasswd;
    access_log ${NGINXLOGDIR}access.awstats.log;
    error_log ${NGINXLOGDIR}error.awstats.log;
    rewrite ^/stats/(.*)\$  /\$1 break;
  }

  location /newapi/ {
    # Not available for hotlinking
    valid_referers server_names;
    if (\$invalid_referer) {
      return 444;
    }

    proxy_pass_header Server;
    proxy_set_header Host \$http_host;
    proxy_set_header  X-Real-IP  \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_redirect off;
    proxy_pass http://localhost:${PORTAPI};

    # Upgrade to support websockets
    proxy_http_version 1.1;
    proxy_set_header Upgrade \$http_upgrade;
    proxy_set_header Connection "upgrade";

    # Default timeout is 60s
    # proxy_read_timeout 60s;

    rewrite ^/newapi/(.*)\$  /\$1 break;
  }

  location ~* ^/newapi/puzzle/.*/piece/.*/move/ {
    # Limit to max of 4 simultaneous puzzle piece moves per ip addr
    #limit_conn   addr 4;
    # Not exactly sure why, but setting it to 4 will not allow more then 3 players on a single IP.
    # This is set to 40 to allow at most 39 players on one IP
    limit_conn   addr 40;

    keepalive_timeout 0;
    limit_req zone=piece_move_limit_per_ip burst=60 nodelay;
    # Drop connection instead of showing 503
    limit_req_status 444;

    # Not available for hotlinking
    valid_referers server_names;
    if (\$invalid_referer) {
      return 444;
    }

    proxy_pass_header Server;
    proxy_set_header Host \$http_host;
    proxy_set_header  X-Real-IP  \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_redirect off;
    proxy_pass http://localhost:${PORTAPI};

    rewrite ^/newapi/(.*)\$  /\$1 break;
  }

  location ~* ^/newapi/user-login/.*/ {
    # For just this url; don't restrict by referrers
    proxy_pass_header Server;
    proxy_set_header Host \$http_host;
    proxy_set_header  X-Real-IP  \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_redirect off;
    proxy_pass http://localhost:${PORTAPI};

    rewrite ^/newapi/(.*)\$  /\$1 break;
  }

  location /newapi/admin/ {
    # Not available for hotlinking
    valid_referers server_names;
    if (\$invalid_referer) {
      return 444;
    }

    # Set to droplet ip not floating ip.
    # Requires using SOCKS proxy (ssh -D 8080 user@host)
    #allow 67.207.90.241;
    #deny all;

    proxy_pass_header Server;
    proxy_set_header Host \$http_host;
    proxy_set_header  X-Real-IP  \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_redirect off;
    proxy_pass http://localhost:${PORTAPI};

    auth_basic "Restricted Content";
    auth_basic_user_file ${SRVDIR}.htpasswd;

    rewrite ^/newapi/(.*)\$  /\$1 break;
  }

  location /divulge/ {
    proxy_pass_header Server;
    proxy_set_header Host \$http_host;
    proxy_set_header  X-Real-IP  \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_redirect off;
    proxy_pass http://localhost:${PORTDIVULGER};

    # Upgrade to support websockets
    proxy_http_version 1.1;
    proxy_set_header Upgrade \$http_upgrade;
    proxy_set_header Connection "upgrade";

    # Default timeout is 60s
    # proxy_read_timeout 60s;
  }

  location ~* ^/chill/site/puzzle/.*\$ {
    proxy_pass_header Server;
    proxy_set_header Host \$http_host;
    proxy_set_header  X-Real-IP  \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;

    ## Don't use cache for puzzle page
    proxy_set_header Chill-Skip-Cache 1;

    proxy_redirect off;
    proxy_pass http://localhost:${PORTCHILL};
    rewrite ^/chill/(.*)\$  /\$1 break;
  }

  location /chill/ {
    proxy_pass_header Server;
    proxy_set_header Host \$http_host;
    proxy_set_header  X-Real-IP  \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;

    ## Prevent others from skipping cache
    proxy_set_header Chill-Skip-Cache "";

    proxy_redirect off;
    proxy_pass http://localhost:${PORTCHILL};
    rewrite ^/chill/(.*)\$  /\$1 break;
  }

  location /chill/site/admin/ {

    # Set to droplet ip not floating ip.
    # Requires using SOCKS proxy (ssh -D 8080 user@host)
    #allow 67.207.90.241;
    #deny all;

    proxy_pass_header Server;
    proxy_set_header Host \$http_host;
    proxy_set_header  X-Real-IP  \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;

    ## Skip cache on admin pages
    proxy_set_header Chill-Skip-Cache 1;

    proxy_redirect off;
    proxy_pass http://localhost:${PORTCHILL};

    auth_basic "Restricted Content";
    auth_basic_user_file ${SRVDIR}.htpasswd;

    rewrite ^/chill/(.*)\$  /\$1 break;
  }

  location /theme/ {
    rewrite ^/theme/(.*)\$  /chill/theme/\$1;
  }
  location /media/ {
    # Not available for hotlinking
    valid_referers server_names;
    if (\$invalid_referer) {
      return 444;
    }
    rewrite ^/media/(.*)\$  /chill/media/\$1;
  }

  location /media/bit-icons/ {
    #rewrite ^/media/(.*)\$
    root ${SRVDIR};
  }

  location ~* ^/resources/.*/(scale-100/raster.png|scale-100/raster.css)\$ {
    # Public resources except preview_full.jpg
    # Not available for hotlinking
    valid_referers server_names;
    if (\$invalid_referer) {
      return 444;
    }
    #root /mnt/volume-nyc1-01;
    root ${SRVDIR};

  }
  location ~* ^/resources/.*/(preview_full.jpg)\$ {
    # Allow hotlinking
    #root /mnt/volume-nyc1-01;
    root ${SRVDIR};
  }


error_page 500 501 502 503 504 505 506 507 /error_page.html;
location  /error_page.html {
  internal;
}

error_page 401 /unauthorized_page.html;
location /unauthorized_page.html {
  internal;
}

error_page 404 /notfound_page.html;
location /notfound_page.html {
    internal;
}

HERE

if test "${ENVIRONMENT}" == 'development'; then

cat <<HEREBEDEVELOPMENT
  # certs for localhost only
  #ssl_certificate /etc/nginx/ssl/server.crt;
  #ssl_certificate_key /etc/nginx/ssl/server.key;

  server_name local-puzzle-massive;
HEREBEDEVELOPMENT

else

if test -e .has-certs; then
cat <<HEREENABLESSLCERTS
  # certs created from certbot
  #ssl_certificate /etc/letsencrypt/live/puzzle.massive.xyz/fullchain.pem;
  #ssl_certificate_key /etc/letsencrypt/live/puzzle.massive.xyz/privkey.pem;
HEREENABLESSLCERTS
else
cat <<HERETODOSSLCERTS
  # certs can be created from running 'bin/provision-certbot.sh ${SRVDIR}'
  # TODO: uncomment after they exist
  #ssl_certificate /etc/letsencrypt/live/puzzle.massive.xyz/fullchain.pem;
  #ssl_certificate_key /etc/letsencrypt/live/puzzle.massive.xyz/privkey.pem;
HERETODOSSLCERTS
fi

cat <<HEREBEPRODUCTION

  server_name puzzle-1 puzzle.massive.xyz;

  location /.well-known/ {
    try_files \$uri =404;
  }

  #location / {
  #  root ${SRVDIR}frozen;
  #}
HEREBEPRODUCTION
fi

cat <<HERE
}
HERE

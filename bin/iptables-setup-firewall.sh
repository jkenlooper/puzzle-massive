#!/usr/bin/env bash
set -eu -o pipefail

# More documentation on iptables
# https://www.netfilter.org/documentation/
# https://www.digitalocean.com/community/tutorials/iptables-essentials-common-firewall-rules-and-commands

set -x

## Allow loopback traffic (localhost to localhost)
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

## Allow Established and Related Incoming Connections
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

## Allow Established Outgoing Connections
iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED -j ACCEPT

## Internal to External
iptables -A FORWARD -i eth1 -o eth0 -j ACCEPT

## Drop Invalid Packets
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

## Allow All Incoming SSH
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT
iptables -A OUTPUT -p tcp --sport 22 -m conntrack --ctstate ESTABLISHED -j ACCEPT

### Limit Rate of New SSH Connections
# Verify with netcat by opening a connection 5 times.
# for n in $(seq 5); do test -n "$(echo 'QUIT' | nc -w 3 $REMOTE_IP 22)" || echo 'Connection blocked'; done
iptables -I INPUT -p tcp --dport 22 -i eth0 -m state --state NEW -m recent --set
iptables -I INPUT -p tcp --dport 22 -i eth0 -m state --state NEW -m recent  --update --seconds 60 --hitcount 4 -j DROP

## Allow All Incoming HTTP and HTTPS
iptables -A INPUT -p tcp -m multiport --dports 80,443 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT
iptables -A OUTPUT -p tcp -m multiport --dports 80,443 -m conntrack --ctstate ESTABLISHED -j ACCEPT


## Prevent DoS Attacks
# https://www.netfilter.org/documentation/HOWTO/packet-filtering-HOWTO-7.html

### Syn-flood protection
iptables -A FORWARD -p tcp --syn -m limit --limit 1/s -j ACCEPT

### Furtive port scanner
iptables -A FORWARD -p tcp --tcp-flags SYN,ACK,FIN,RST RST -m limit --limit 1/s -j ACCEPT

### Ping of death
iptables -A FORWARD -p icmp --icmp-type echo-request -m limit --limit 1/s -j ACCEPT


## Prevent user_data from being leaked
# https://security.stackexchange.com/questions/219375/how-to-harden-against-credential-stealing-in-ec2-via-the-http-169-254-169-254
# https://docs.digitalocean.com/products/droplets/how-to/provide-user-data/
# The user_data contains sensitive information and requests to access it via
# creating a http request from dev or www-data users should be blocked. More
# information on SSRF (Server-Side Request Forgery) attacks can be searched for.

# Limiting this across all users including root could break the ability to
# expand the disk size of the droplet as well as recover from snapshot/backup.
# Resizing the RAM and CPU on the droplet should still work. That is why it is
# only being applied to dev and www-data users.
iptables --table filter --insert OUTPUT 1 --destination 169.254.169.254 --match owner --uid-owner dev --jump REJECT --reject-with icmp-admin-prohibited
iptables --table filter --insert OUTPUT 1 --destination 169.254.169.254 --match owner --uid-owner www-data --jump REJECT --reject-with icmp-admin-prohibited


## Save all iptables so they persist after reboot.
netfilter-persistent save

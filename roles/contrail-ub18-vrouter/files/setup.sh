#!/bin/bash -xe

# Some unattended upgrades lock frontend, kill them
sudo kill -9 $(sudo lsof /var/lib/dpkg/lock-frontend | tr -s ' ' | cut -d ' ' -f2 | tail -1)

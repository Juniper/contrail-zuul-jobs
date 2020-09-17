#!/bin/bash -xe

# Update your existing list of packages
sudo apt-get -y update && sleep 30

# Some unattended upgrades lock frontend, kill them
# sudo kill -9 $(sudo lsof /var/lib/dpkg/lock-frontend | tr -s ' ' | cut -d ' ' -f2 | tail -1)

# Next, install a few prerequisite packages which let apt use packages over HTTPS
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg2 software-properties-common

# Then add the GPG key for the official Docker repository to your system
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

# Add the Docker repository to APT sources
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

# Next, update the package database with the Docker packages from the newly added repo
sudo apt-get -y update && sleep 30

# configure insecure registry for ci-repo
# sudo mkdir /etc/docker
# echo '{ "insecure-registries":["10.84.5.81:33325"] }' | sudo tee -a /etc/docker/daemon.json

# Make sure you are about to install from the Docker repo instead of the default Ubuntu repo
sudo apt-cache policy docker-ce

# Finally, install Docker
sudo apt-get install -y docker-ce

# Docker should now be installed, the daemon started
sudo systemctl status docker | cat

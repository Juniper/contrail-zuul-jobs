#!/bin/bash -xe

# update your existing list of packages
sudo apt-get -y update && sleep 30

# some apt processes prevent from proceeding further
sudo killall apt apt-get || true

# Next, install a few prerequisite packages which let apt use packages over HTTPS
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg2 software-properties-common

# Then add the GPG key for the official Docker repository to your system
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

# Add the Docker repository to APT sources
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

# Next, update the package database with the Docker packages from the newly added repo
sudo apt-get -y update && sleep 30

# configure insecure registry for ci-repo
echo "{ \"insecure-registries\":[\"10.84.5.81:33325\"] }" > /etc/docker/daemon.json

# Make sure you are about to install from the Docker repo instead of the default Ubuntu repo
sudo apt-cache policy docker-ce

# Finally, install Docker
sudo apt-get install -y docker-ce

# Docker should now be installed, the daemon started
sudo systemctl status docker

# If you want to avoid typing sudo whenever you run the docker command, add your username to the docker group
# sudo usermod -aG docker ${USER}

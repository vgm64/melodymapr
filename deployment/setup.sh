#!/bin/sh

# Deployment Script for deploying to Ubuntu 12.04 Server

# Installing git and git dependencies, pip, and curl
sudo apt-get update
sudo apt-get build-dep git-core -y
sudo apt-get install git-core python-pip curl nginx -y
sudo pip install pip --upgrade

# Installing node and npm
sudo apt-get install python-software-properties python g++ make
sudo add-apt-repository ppa:chris-lea/node.js
sudo apt-get update
sudo apt-get install nodejs

# Change into home directory
cd ~

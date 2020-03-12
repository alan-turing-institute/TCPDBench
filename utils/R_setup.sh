#!/bin/bash
#
# Setup an R environment in a given directory.
#
# This works as follows. We create an ".Rprofile" file in the current 
# directory that sets the .libPaths to the desired Rlib directory. We do the 
# same with an .Renviron file because it's R so one place isn't enough. This 
# essentially makes that the only source of packages read by anything that 
# respects this .Rprofile. Next we install packages as normal using the 
# install_if_not_exists.R script, which only installs packages if necessary 
# and supports GitHub and local packages as well.
#
# This file is part of RSimpleVenv: https://github.com/GjjvdBurg/RSimpleVenv
#
# Author: G.J.J. van den Burg
# Date: 2019-06-19
# License: MIT

res='\033[1m\033[0m'
log() { echo -e "\e[32m$*${res}"; }
err() { echo -e "\e[31m$*${res}"; exit 1; }

install() {
	log "Installing $1";
	Rscript ./utils/install_if_not_exist.R "$1"
	# exit on failure
	if [ ! $? == 0 ]
	then
		err "Non-zero exit status after installing $1"
	fi
}

if [ $# -ne 2 ]
then
	echo "Usage: $0 packageFile rlib_dir"
	exit 1
fi

PACKAGE_FILE="$1"
LIBDIR=$(realpath "$2")
mkdir -p ${LIBDIR}

# Ensure that this is the only libPath from now on.
echo ".libPaths(c('${LIBDIR}'))" > .Rprofile
echo "R_LIBS=${LIBDIR}" > .Renviron
echo "R_LIBS_USER=${LIBDIR}" >> .Renviron

# Here's a fun one: for some reason R tests lazy loading in vanilla mode by 
# default, which overwrites all the environment and library stuff we just 
# carefully set. This can break things when you have a different package 
# version installed in your user R package library. Luckily, if you dig 
# through the R source code (not in the documentation!), you can find out that 
# there's an obscure environment variable that can be set to disable this 
# behaviour. What fun! What an intuitively designed programming language! /s
export _R_CHECK_INSTALL_DEPENDS_="TRUE"

# Install devtools for GitHub-based packages
install devtools

# Install all packages from the provided package file
while read -r pkg
do
	if [ -z ${pkg} ]
	then
		continue
	fi
	install "${pkg}"
done < ${PACKAGE_FILE}

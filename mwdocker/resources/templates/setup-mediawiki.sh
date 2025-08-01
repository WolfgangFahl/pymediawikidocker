#!/bin/bash
# WF 2025-08-01
# replace Dockerfile based setup
# see https://github.com/WolfgangFahl/pymediawikidocker/issues/84

set -e

# Script directory as parameter (default fallback)
SCRIPT_DIR="${1:-/scripts}"
WEB_DIR="/var/www/html"


#ansi colors
#http://www.csc.uvic.ca/~sae/seng265/fall04/tips/s265s047-tips/bash-using-colors.html
blue='\033[0;34m'
red='\033[0;31m'
green='\033[0;32m' # '\e[1;32m' is too bright for white bg.
endColor='\033[0m'

#
# a colored message
#   params:
#     1: l_color - the color of the message
#     2: l_msg - the message to display
#
color_msg() {
  local l_color="$1"
  local l_msg="$2"
  echo -e "${l_color}$l_msg${endColor}"
}

#
# error
#
# show the given error message on stderr and exit
#
#   params:
#     1: l_msg - the error message to display
#
error() {
  local l_msg="$1"
  # use ansi red for error
  color_msg $red "Error:" 1>&2
  color_msg $red "\t$l_msg" 1>&2
  exit 1
}

#
# download the language images to the given image directory
#
lang_images () {
  local l_target="$1"
  if [ ! -d $l_target ]
  then
    error "image directory $l_target does not exist"
  fi
  from=http://semantic-mediawiki.org/w/
  for img in images/e/e7/Lang-De.gif images/7/78/Lang-En.gif images/6/61/Lang-Es.gif images/f/f0/Lang-Fr.gif images/9/95/Lang-Ja.gif images/c/cb/Lang-Nl.gif images/3/38/Lang-Ru.gif images/8/85/Lang-Zh-hans.gif images/2/20/Lang-Uk.gif
  do
    imgpath=`echo $img | cut -f1-3 -d/`
    imgname=`echo $img | cut -f4 -d/`
    if [ ! -f $l_target/$img ]
    then
      color_msg $blue "downloading $imgname ..."
      mkdir -p $l_target/$imgpath
      curl -L -s -o $l_target/$img $from/$img
      chown www-data:www-data $imgpath
    else
      color_msg $green "$imgname already downloaded"
   fi
  done
}

#
# run the update script
#
run_update() {
	php maintenance/update.php --skip-config-validation --quick
	# work around possible version problem - older MediaWiki versions do no thave
	# --skip-config-validation and will signal an error
	if [ $? -ne 0 ]
	then
	  # if an error occured simply retry - no matter whether the syntax error above was
	  # the cause or any other error - no harm done except some extra time ...
	  php maintenance/update.php --quick
	fi
}


#
# make sure we use proper permissions
#
fix_permissions() {
  chown -R www-data ${WEB_DIR}
  chgrp -R www-data ${WEB_DIR}
}

#
# start the run jobs
#
start_runJobs() {
	jobs=$(pgrep -fla runjobs | wc -l)
	if [ $jobs -gt 3 ]
	then
	  echo "$jobs runjobs already running ..."
	  exit 1
	fi
	php maintenance/runJobs.php >> /var/log/mediawiki/runJobs.log 2>&1
}

#
# initialize the database
#
initdb() {
  # get the database password from Localsettings.php
  password=$(grep wgDBpassword /var/www/html/LocalSettings.php  | cut -f2 -d'"')
  # initialize the database from the sql backup
  cat ${SCRIPT_DIR}/wiki.sql  | mysql --host db -u wikiuser wiki --password="$password"
}

echo "Setting up MediaWiki using scripts from: ${SCRIPT_DIR}"

# Update MediaWiki extensions via composer
cd ${WEB_DIR}
composer update --no-dev

# Run other setup scripts
chmod +x ${SCRIPT_DIR}/*.sh

# copy LocalSettings.php
if [ ! -f ${WEB_DIR}/LocalSettings.php ]
then
  cp -p ${SCRIPT_DIR}/LocalSettings.php ${WEB_DIR}/LocalSettings.php
fi

# fix permissions before starting
fix_permissions

# install extensions which are not installed via compose
${SCRIPT_DIR}/installExtensions.sh

# fix permissions again
fix_permissions

# call initialize database function
initdb

${SCRIPT_DIR}/addSysopUser.sh
${SCRIPT_DIR}/addCronTabEntry.sh

# run the update script
run_update

# install language images
lang_images ${WEB_DIR}/images
# fix permissions before finishing
fix_permissions

echo "MediaWiki setup complete!"
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
  if [ ! -d "$l_target" ]; then
    error "image directory $l_target does not exist"
  fi
  local from="http://semantic-mediawiki.org/w/"
  local imgs=(
    images/e/e7/Lang-De.gif images/7/78/Lang-En.gif images/6/61/Lang-Es.gif
    images/f/f0/Lang-Fr.gif images/9/95/Lang-Ja.gif images/c/cb/Lang-Nl.gif
    images/3/38/Lang-Ru.gif images/8/85/Lang-Zh-hans.gif images/2/20/Lang-Uk.gif
  )

  for img in "${imgs[@]}"; do
    local imgpath="$(dirname "$img")"
    local imgname="$(basename "$img")"
    local fullpath="$l_target/$img"

    if [ ! -f "$fullpath" ]; then
      color_msg "$blue" "downloading $imgname ..."
      mkdir -p "$l_target/$imgpath"
      curl -L -s -o "$fullpath" "$from/$img"
      chown www-data:www-data "$l_target/$imgpath"
    else
      color_msg "$green" "$imgname already downloaded"
    fi
  done
}


#
# run the update script
#
run_update() {
  local options="--quick"
  if php maintenance/update.php --help | grep -q -- --skip-config-validation; then
    options="--skip-config-validation $options"
  fi
  php maintenance/update.php $options
}


#
# make sure we use proper permissions
#
fix_permissions() {
  chown -R www-data ${WEB_DIR}
  chgrp -R www-data ${WEB_DIR}
}


# add crontab entry
# run startRunJobs.sh every minute
# prepare logging
add_crontab_entry() {
	mkdir -p /var/log/mediawiki
	touch /var/log/mediawiki/runJobs.log
	# add an entry for the crontab
	(crontab -l 2>/dev/null; echo "*/1 * * * * /root/startRunJobs.sh") | crontab -
	# start the cron service
	service cron start
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

# copy LocalSettings.php and phpinfo.php
for script in LocalSettings.php phpinfo.php
do
  if [ ! -f ${WEB_DIR}/$script ]
  then
    cp -p ${SCRIPT_DIR}/$script ${WEB_DIR}/$script
  fi
done

# fix permissions before starting
fix_permissions

# call initialize database function
initdb

# run the update script
run_update

# install extensions which are not installed via compose
${SCRIPT_DIR}/installExtensions.sh

# fix permissions again
# mostly to avoid the never ending story of
# https://github.com/SemanticMediaWiki/SemanticMediaWiki/issues/4785
# Semantic MediaWiki was installed and enabled but is missing an appropriate upgrade key.
fix_permissions

# run the update script again
run_update

${SCRIPT_DIR}/addSysopUser.sh

# install language images
lang_images ${WEB_DIR}/images

# fix permissions again before finishing
fix_permissions

# make sure we start runjobs every minute for updates
add_crontab_entry

echo "MediaWiki setup complete!"
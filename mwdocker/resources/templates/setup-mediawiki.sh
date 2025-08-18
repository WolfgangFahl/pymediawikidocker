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
# show usage information
#
usage() {
  cat << EOF
Usage: $0 [OPTIONS]

MediaWiki setup script with modular execution options.

GENERAL OPTIONS:
  --script-dir DIR      Directory containing setup files (default: /scripts)
  --web-dir DIR         MediaWiki web root (default: /var/www/html)
  -h, --help            Show this help

STEPS (choose any; default is --all if none given):
  --all                 Run all steps (default)
  --install-files       Install config and utility files
  --initdb              Initialize database from SQL backup
  --extensions          Install MediaWiki extensions (installExtensions.sh)
  --permissions         Fix file permissions
  --composer            Update extensions via composer
  --update              Run MediaWiki update script
  --sysop               Add sysop user
  --lang-images         Download language images
  --crontab             Add crontab entry for runJobs
  --start-runjobs       Start a single runJobs execution now

Examples:
  $0 --all
  $0 --script-dir /custom/scripts --initdb --permissions
  $0 --help
EOF
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
  sudo chown -R www-data ${WEB_DIR}
  sudo chgrp -R www-data ${WEB_DIR}
}


# add crontab entry
# run startRunJobs.sh every minute
# prepare logging
add_crontab_entry() {
  sudo mkdir -p /var/log/mediawiki
  sudo touch /var/log/mediawiki/runJobs.log
  sudo chown www-data:www-data /var/log/mediawiki/runJobs.log

  local cron_job="*/1 * * * * /root/startRunJobs.sh"
  local tmp_cron="/tmp/current_cron"

  # get current crontab (if any), excluding our line
  if crontab -l 2>/dev/null | grep -vF "$cron_job" > "$tmp_cron"; then
    true  # successful read
  else
    touch "$tmp_cron"
  fi

  echo "$cron_job" >> "$tmp_cron"
  crontab "$tmp_cron"
  rm -f "$tmp_cron"

  sudo service cron start
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

# initialize the database
initdb() {
  # get DB connection details from LocalSettings.php
  password=$(grep wgDBpassword /var/www/html/LocalSettings.php | cut -d'"' -f2)
  user=$(grep wgDBuser /var/www/html/LocalSettings.php | cut -d'"' -f2)
  dbname=$(grep wgDBname /var/www/html/LocalSettings.php | cut -d'"' -f2)

  # initialize the database from the sql backup
  cat "${SCRIPT_DIR}/wiki.sql" | mysql --host=db -u"$user" -p"$password" "$dbname"
}


#
# install config and utility files with correct ownership and permissions
#
install_files() {
	local files_with_perms=(
	  "LocalSettings.php:644"
	  "phpinfo.php:755"
	  "composer.local.json:644"
	)

	for entry in "${files_with_perms[@]}"; do
	  file="${entry%%:*}"
	  mode="${entry##*:}"
	  src="${SCRIPT_DIR}/${file}"
	  dest="${WEB_DIR}/${file}"

	  if [ ! -f "$dest" ]; then
	    install -m "$mode" -o www-data -g www-data "$src" "$dest"
	  fi
	done
}

# run all steps
all() {
echo "Setting up MediaWiki using scripts from: ${SCRIPT_DIR}"

# make sure we copy installation files from script dir
install_files

cd ${WEB_DIR}
# call initialize database function
initdb

# install extensions which are not installed via composer
cd ${WEB_DIR}/extensions

# the generated script will have the specific list of extensions for this
# wiki
${SCRIPT_DIR}/installExtensions.sh

# fix permissions
fix_permissions

cd ${WEB_DIR}
# Update MediaWiki extensions via composer
# composer.local.json was installed earlier to make this work
composer update --no-dev


# run the update script to initialize tables e.g. for Semanticmediawiki
# also we need to avoid the never ending story of
# https://github.com/SemanticMediaWiki/SemanticMediaWiki/issues/4785
# Semantic MediaWiki was installed and enabled but is missing an appropriate upgrade key.
run_update

# make sure we have an initial user to work with
# user wikiCMS/tsite and ProfiWiki if you need to more control
${SCRIPT_DIR}/addSysopUser.sh

# install language images
lang_images ${WEB_DIR}/images

# fix permissions again before finishing
fix_permissions

# make sure we start runjobs every minute for updates
add_crontab_entry

echo "MediaWiki setup complete!"
}

# default: show help if no args
[ $# -eq 0 ] && { usage; exit 0; }

for arg in "$@"; do
  case "$arg" in
    --script-dir) shift; SCRIPT_DIR="$1";;
    --install-files) install_files ;;
    --initdb)        initdb ;;
    --extensions)    ${SCRIPT_DIR}/installExtensions.sh ;;
    --permissions)   fix_permissions ;;
    --composer)      composer update --no-dev ;;
    --update)        run_update ;;
    --sysop)         ${SCRIPT_DIR}/addSysopUser.sh ;;
    --lang-images)   lang_images "${WEB_DIR}/images" ;;
    --crontab)       add_crontab_entry ;;
    --start-runjobs) start_runJobs ;;
    --all)           all ;;
    -h|--help)       usage; exit 0 ;;
    *) echo "Unknown option: $arg"; usage; exit 1 ;;
  esac
done

for arg in "$@"; do
  case "$arg" in
    --script-dir) shift; SCRIPT_DIR="$1";;
    --install-files) install_files ;;
    --initdb)        initdb ;;
    --extensions)    do_extensions ;;
    --permissions)   fix_permissions ;;
    --composer)      do_composer_update ;;
    --update)        run_update ;;
    --sysop)         do_sysop ;;
    --lang-images)   lang_images "${WEB_DIR}/images" ;;
    --crontab)       add_crontab_entry ;;
    --start-runjobs) start_runJobs ;;
    --all)           all();;
    -h|--help)       usage; exit 0 ;;
    *) echo "Unknown option: $arg"; usage; exit 1 ;;
  esac
done
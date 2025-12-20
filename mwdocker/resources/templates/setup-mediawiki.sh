#!/bin/bash
# WF 2025-08-01
# replace Dockerfile based setup
# see https://github.com/WolfgangFahl/pymediawikidocker/issues/84

# Robustness: Exit on error, unset vars, or pipe failure
set -euo pipefail

# Determine execution context (root vs sudo)
SUDO=""
if [ "$EUID" -ne 0 ]; then
    SUDO="sudo"
fi

# Robustness: Logging Configuration
LOG_DIR="/var/log/mediawiki"
LOG_FILE="${LOG_DIR}/setup.log"

# Ensure log directory exists
if [ ! -d "$LOG_DIR" ]; then
    $SUDO mkdir -p "$LOG_DIR"
    $SUDO chown www-data:www-data "$LOG_DIR"
fi

# Redirect stdout/stderr to log file and console
exec > >(tee -a "${LOG_FILE}") 2>&1

# Robustness: Trap errors
trap 'cmd=$BASH_COMMAND; echo "Error: Command \"$cmd\" failed at line $LINENO."' ERR

# load system-wide profile so PATH is set like in interactive shells
if [ -f /etc/profile ]; then
    source /etc/profile
fi

# global directories - may be modified with options
SCRIPT_DIR="/scripts"
WEB_DIR="/var/www/html"
SETTINGS="LocalSettings.php"
MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD:-}


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


GENERAL OPTIONS:
  --script-dir DIR      Directory containing setup files (default: /scripts)
  --web-dir DIR         MediaWiki web root (default: /var/www/html)
  --settings FILENAME   LocalSettings.php file name
  -h, --help            Show this help

STEPS (choose any; default is --all if none given):
  --all                 Run all steps (default)
  --install-files       Install config and utility files
  --initdb              Initialize database from SQL backup
  --grant               Grant database permissions
  --mysql-root-password PWD  MySQL root password for grants
  --extensions          Install MediaWiki extensions (installExtensions.sh)
  --permissions         Fix file permissions
  --composer            Update extensions via composer
  --update              Run MediaWiki update script
  --short-urls          Write .htaccess to enable /Page short URLs (no /wiki/)
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
  #local from="https://semantic-mediawiki.org/w/"
  local from="https://wiki.bitplan.com/"
  # all language images to download
  local imgs=(
    e/e7/Lang-De.gif 7/78/Lang-En.gif 6/61/Lang-Es.gif
    f/f0/Lang-Fr.gif 9/95/Lang-Ja.gif c/cb/Lang-Nl.gif
    3/38/Lang-Ru.gif 8/85/Lang-Zh-hans.gif 2/20/Lang-Uk.gif
  )

  for rel in "${imgs[@]}"; do
    local fullpath="$l_target/$rel"
    local dirpath="$(dirname "$fullpath")"
    if [ ! -f "$fullpath" ]; then
      color_msg "$blue" "downloading $(basename "$rel") ..."
      mkdir -p "$dirpath"
      # Robustness: Added retry logic to fix exit code 35 (SSL handshake/network errors)
      curl --retry 3 --retry-delay 2 --retry-connrefused -fLsS -o "$fullpath" "$from/images/$rel"
      $SUDO chown www-data:www-data "$dirpath" "$fullpath"
    else
      color_msg "$green" "$(basename "$rel") already present"
    fi
  done
}


#
# run the update script
#
run_update() {
  local options="--quick"

  if [ ! -f "${WEB_DIR}/maintenance/update.php" ]; then
    error "maintenance/update.php not found at ${WEB_DIR}/maintenance/update.php"
  fi

  # Change to web directory to ensure relative paths work
  cd "${WEB_DIR}"

  if php maintenance/update.php --help | grep -q -- --skip-config-validation; then
    options="--skip-config-validation $options"
  fi
  # Capture stderr to log
  php maintenance/update.php $options
}


#
# make sure we use proper permissions
#
fix_permissions() {
  $SUDO chown -R www-data "${WEB_DIR}"
  $SUDO chgrp -R www-data "${WEB_DIR}"
  # Ensure composer home directory exists with correct structure
  local COMPOSER_DIR="${WEB_DIR}/.composer"
  $SUDO mkdir -p "${COMPOSER_DIR}/cache"
  $SUDO chown -R www-data "${COMPOSER_DIR}"
  $SUDO chgrp -R www-data "${COMPOSER_DIR}"
}


# add crontab entry
# run startRunJobs.sh every minute
# prepare logging
add_crontab_entry() {
  $SUDO mkdir -p /var/log/mediawiki
  $SUDO touch /var/log/mediawiki/runJobs.log
  $SUDO chown www-data:www-data /var/log/mediawiki/runJobs.log

  local cron_job="*/1 * * * * /scripts/setup-mediawiki.sh --start-runjobs"
  local tmp_cron="/tmp/current_cron"

  # get current crontab (if any), excluding our line
  # Robustness: handle case where crontab is empty
  if crontab -l 2>/dev/null | grep -vF "$cron_job" > "$tmp_cron"; then
    true  # successful read
  else
    touch "$tmp_cron"
  fi

  echo "$cron_job" >> "$tmp_cron"
  crontab "$tmp_cron"
  rm -f "$tmp_cron"

  # Robustness: Only start service if it exists (some minimal docker images lack init)
  if command -v service >/dev/null 2>&1 && [ -f /etc/init.d/cron ]; then
    $SUDO service cron start
  fi
}

#
# start the run jobs
#
start_runJobs() {
  jobs=$(pgrep -fla runjobs | wc -l)
  if [ "$jobs" -gt 3 ]
  then
    echo "$jobs runjobs already running ..."
    # Exit cleanly if too many jobs, not an error
    exit 0
  fi
  cd "${WEB_DIR}"
  php maintenance/runJobs.php >> /var/log/mediawiki/runJobs.log 2>&1
}

#
# mysql connection details from LocalSettings.php as specified in $SETTINGS
#
get_mysql_connection() {
  # Extract DB connection details from LocalSettings.php
  # of the script directory (as generated by pymediawikidocker)
  local settings="${SCRIPT_DIR}/${SETTINGS}"
  if [ ! -f "$settings" ]; then
    error "Settings file $settings not found."
  fi
  DB_PASSWORD=$(grep wgDBpassword "$settings" | cut -d'"' -f2)
  DB_USER=$(grep wgDBuser "$settings" | cut -d'"' -f2)
  DB_NAME=$(grep wgDBname "$settings" | cut -d'"' -f2)
}

#
# Robustness: Wait for database to be ready
#
wait_for_db() {
  local host="db"
  local user="$1"
  local pass="$2"
  local max_retries=60
  local count=0

  color_msg "$blue" "Waiting up to $max_retries for database connection..."
  while ! mysql --host="$host" -u"$user" -p"$pass" -e "SELECT 1;" >/dev/null 2>&1; do
    sleep 1
    echo -n "."
    count=$((count + 1))
    if [ $count -ge $max_retries ]; then
      error "Timed out waiting for database connection."
    fi
  done
  color_msg "$green" "Database connected."
}

# grant permissions for non root user as declared in $SETTINGS
grant_permissions() {
  if [ -z "${MYSQL_ROOT_PASSWORD}" ]; then
    error "MySQL root password not provided. Use --mysql-root-password option or set in Environment"
  fi
  get_mysql_connection

  # Wait for DB using root credentials
  wait_for_db "root" "${MYSQL_ROOT_PASSWORD}"

  mysql --host=db -uroot -p"${MYSQL_ROOT_PASSWORD}" <<EOF
CREATE DATABASE IF NOT EXISTS ${DB_NAME};
CREATE USER IF NOT EXISTS '${DB_USER}'@'%' IDENTIFIED BY '${DB_PASSWORD}';
ALTER USER '${DB_USER}'@'%' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'%';
FLUSH PRIVILEGES;
EOF
  # Verify user can connect
  if  mysql --host=db -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "SELECT 1;" >/dev/null 2>&1; then
     color_msg "$green" "$DB_NAME accessible for $DB_USER"
  else
    error "User ${DB_USER} cannot access database ${DB_NAME}"
  fi
}


#
# initialize the Mediawiki database content with the needed table structure
#
initdb() {
  get_mysql_connection

  # Check if SQL file exists
  if [ ! -f "${SCRIPT_DIR}/wiki.sql" ]; then
    error "SQL file not found: ${SCRIPT_DIR}/wiki.sql"
  fi

  # Test database connection first
  wait_for_db "$DB_USER" "$DB_PASSWORD"

  # Import with error handling
  if cat "${SCRIPT_DIR}/wiki.sql" | mysql --host=db -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME"; then
    color_msg "$green" "Database initialized successfully"
  else
    error "Failed to initialize database from wiki.sql"
  fi
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

      # Check if src exists to allow partial updates
      if [ -f "$src" ]; then
	    if [ ! -f "$dest" ]; then
	      install -m "$mode" -o www-data -g www-data "$src" "$dest"
	    fi
      else
        echo "Warning: Source file $src missing."
      fi
	done
}

#
# install extensions not managed via composer
#
do_extensions() {
  cd "${WEB_DIR}/extensions"
  if [ -x "${SCRIPT_DIR}/installExtensions.sh" ]; then
     "${SCRIPT_DIR}/installExtensions.sh"
  fi
}

#
# composer update for extensions managed via composer.local.json
#
do_composer_update() {
  cd "${WEB_DIR}"
  if command -v composer >/dev/null 2>&1; then
      composer update --no-dev
  else
      error "Composer not found in path"
  fi
}


#
# add initial sysop user
#
do_sysop() {
  # make sure we have an initial user to work with
  # use wikiCMS/tsite and ProfiWiki if you need to more control
  if [ -x "${SCRIPT_DIR}/addSysopUser.sh" ]; then
      "${SCRIPT_DIR}/addSysopUser.sh"
  fi
}

#
# enable short URLs via .htaccess (no /wiki prefix), root install
# Writes ${WEB_DIR}/.htaccess and sets proper ownership/permissions.
#
short_urls_htaccess() {
  local ht="${WEB_DIR}/.htaccess"
  cat >"$ht" <<'EOF'
RewriteEngine On

# serve existing files/dirs (api.php, load.php, resources/, images/, etc.)
RewriteCond %{REQUEST_FILENAME} -f [OR]
RewriteCond %{REQUEST_FILENAME} -d
RewriteRule ^ - [L]

# root -> Main Page
RewriteRule ^$ index.php [L]

# everything else -> title
RewriteRule ^(.+)$ index.php?title=$1 [L,QSA]
EOF
  $SUDO chown www-data:www-data "$ht"
  chmod 0644 "$ht"
  color_msg "$green" "Short URLs enabled via .htaccess."
}


#
# run all MediaWiki setup steps
#
all() {
	echo "Setting up MediaWiki using scripts from: ${SCRIPT_DIR}"

	# make sure we copy installation files from script dir
	install_files

	cd "${WEB_DIR}"
	# call initialize database function
	initdb

	# install non composer extensions
	do_extensions

	# fix permissions
	fix_permissions

	# install composer based extensions
	do_composer_update


	# run the update script to initialize tables e.g. for Semanticmediawiki
	run_update

	# add sysop user
	do_sysop

	# allow short urls
	short_urls_htaccess

	# install language images
	lang_images "${WEB_DIR}/images"

	# fix permissions again before finishing
	fix_permissions

	# make sure we start runjobs every minute for updates
	add_crontab_entry

	echo "MediaWiki setup complete!"
}

# default: show help if no args
[ $# -eq 0 ] && { usage; exit 0; }

# Set Composer home to prevent /var/www/.composer permission errors
export COMPOSER_HOME="${WEB_DIR}/.composer"

while [[ $# -gt 0 ]]; do
  option="$1"
  case "$option" in
   	--script-dir)    export SCRIPT_DIR="${2:?missing DIR}"; shift ;;
    --web-dir)
    	export WEB_DIR="${2:?missing DIR}";
    	shift
    	export COMPOSER_HOME="${WEB_DIR}/.composer"
    	;;
    --settings)      export SETTINGS="${2:?missing FILE}";  shift ;;
    --mysql-root-password) export MYSQL_ROOT_PASSWORD="${2:?missing PWD}"; shift ;;
    --install-files) install_files ;;
    --initdb)        initdb ;;
    --grant)         grant_permissions;;
    --extensions)    do_extensions ;;
    --permissions)   fix_permissions ;;
    --composer)      do_composer_update ;;
    --update)        run_update ;;
    --short-urls)    short_urls_htaccess ;;
    --sysop)         do_sysop ;;
    --lang-images)   lang_images "${WEB_DIR}/images" ;;
    --crontab)       add_crontab_entry ;;
    --start-runjobs) start_runJobs ;;
    --all)           all;;
    -h|--help)       usage; exit 0 ;;
    *) echo "Unknown option: $option"; usage; exit 1 ;;
  esac
  shift
done
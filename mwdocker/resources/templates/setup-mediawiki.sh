#!/bin/bash
# WF 2025-08-01
# replace Dockerfile based setup
# see https://github.com/WolfgangFahl/pymediawikidocker/issues/84
set -e

# Script directory as parameter (default fallback)
SCRIPT_DIR="${1:-/scripts}"
WEB_DIR="/var/www/html"

echo "Setting up MediaWiki using scripts from: ${SCRIPT_DIR}"


# Update MediaWiki extensions via composer
cd ${WEB_DIR}
composer update --no-dev

# Run other setup scripts
chmod +x ${SCRIPT_DIR}/*.sh
${SCRIPT_DIR}/fixPermissions.sh
${SCRIPT_DIR}/installExtensions.sh

${SCRIPT_DIR}/initdb.sh
${SCRIPT_DIR}/addSysopUser.sh
${SCRIPT_DIR}/addCronTabEntry.sh
${SCRIPT_DIR}/update.sh


echo "MediaWiki setup complete!"
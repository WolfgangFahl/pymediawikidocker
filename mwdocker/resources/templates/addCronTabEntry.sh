#!/bin/bash
# WF 2021-07-05
# add crontab entry
# run startRunJobs.sh every minute
# prepare logging
mkdir -p /var/log/mediawiki
touch /var/log/mediawiki/runJobs.log
# add an entry for the crontab
(crontab -l 2>/dev/null; echo "*/1 * * * * /root/startRunJobs.sh") | crontab -
# start the cron service
service cron start
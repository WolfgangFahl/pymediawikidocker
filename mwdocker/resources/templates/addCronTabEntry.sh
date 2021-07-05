#!/bin/bash
# WF 2021-07-05
# add crontab entry
# run startRunJobs.sh every minute
# prepare logging
mkdir -p /var/log/mediawiki
touch /var/log/mediawiki/runJobs.log
(crontab -l 2>/dev/null; echo "*/1 * * * * /root/startRunJobs.sh") | crontab -
service cron start
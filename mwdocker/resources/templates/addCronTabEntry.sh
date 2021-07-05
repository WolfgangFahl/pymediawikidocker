#!/bin/bash
# WF 2021-07-05
# add crontab entry
# run startRunJobs.sh every minute
mkdir -p /var/log/mediawiki
(crontab -l 2>/dev/null; echo "*/1 * * * * /root/startRunJobs.sh") | crontab -
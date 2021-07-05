#!/bin/bash
# WF 2021-07-05
jobs=$(pgrep -fla runjobs | wc -l)
if [ $jobs -gt 3 ]
then
  echo "$jobs runjobs already running ..."
  exit 1
fi
cd /var/www/html

/usr/local/bin/php maintenance/runJobs.php >> /var/log/mediawiki/runJobs.log 2>&1
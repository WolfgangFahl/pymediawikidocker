#!/bin/bash
# add a sysop user 
# WF 2021-06-23
cd /var/www/html
php maintenance/createAndPromote.php --force --sysop "{{user}}" "{{password}}"
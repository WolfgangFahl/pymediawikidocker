#!/bin/bash
# Initialize the MediaWiki database
# WF 2021-06-20
# get the database password from Localsettings.php
password=$(grep wgDBpassword /var/www/html/LocalSettings.php  | cut -f2 -d'"')
# initialize the database from the sql backup
cat /tmp/wiki.sql  | mysql --host db -u wikiuser wiki --password="$password"


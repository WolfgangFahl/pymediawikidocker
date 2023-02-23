#!/bin/bash
# run the MediaWiki update script
# WF 2021-06-22
cd /var/www/html
php maintenance/update.php --skip-config-validation
# work around possible version problem - oder MediaWiki versions do no thave
# --skip-config-validation and will signal an error
if [ $? -ne 0 ]
then
  # if an error occured simply retry - no matter whether the syntax error above was
  # the cause or any other error - no harm done except some extra time ...
  php maintenance/update.php
fi

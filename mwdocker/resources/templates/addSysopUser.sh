#!/bin/bash
# add a sysop user 
# WF 2021-06-23
cd /var/www/html
cAP=maintenance/createAndPromote.php
php $cAP --force --sysop "{{user}}" "{{password}}"
php $cAP --bureaucrat --interface-admin "{{user}}"
grep enableSemantics LocalSettings.php > /dev/null
if [ $? -eq 0 ]
then 
  php $cAP --custom-groups smwAdminstrator "{{user}}"
fi
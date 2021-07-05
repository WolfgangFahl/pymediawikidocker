#!/ bin/bash
# WF 2021-07-05
jobs=$(pgrep -fla runjobs | wc -l)
if [ $jobs -gt 3 ]
then
  echo "$jobs runjobs already running ..."
  exit 1
fi

php maintainance/runjobs.php
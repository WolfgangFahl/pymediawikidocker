#!/bin/bash
#
#   Copyright (C) 2015-2023 BITPlan GmbH
#   http://www.bitplan.com
# 
#   WF 2015-11-08
#
 
#
# get language icons from semantic-mediawiki-org
# Since: 2015-11-08
#
 
#ansi colors
#http://www.csc.uvic.ca/~sae/seng265/fall04/tips/s265s047-tips/bash-using-colors.html
blue='\033[0;34m'
red='\033[0;31m'
green='\033[0;32m' # '\e[1;32m' is too bright for white bg.
endColor='\033[0m'
 
#
# a colored message 
#   params:
#     1: l_color - the color of the message
#     2: l_msg - the message to display
#
color_msg() {
  local l_color="$1"
  local l_msg="$2"
  echo -e "${l_color}$l_msg${endColor}"
}
 
#
# error
#
# show the given error message on stderr and exit
#
#   params:
#     1: l_msg - the error message to display
#
error() {
  local l_msg="$1"
  # use ansi red for error
  color_msg $red "Error:" 1>&2
  color_msg $red "\t$l_msg" 1>&2
  exit 1
}
 
#
# show usage
#
usage() {
  echo "usage: lang"
  # -h|--help|usage|show this usage
  echo "  -h|--help: show this usage"
  # -s|--site|lang_images|download the language images to the given site
  echo "  -s|--site [site]: download the language images to the given site"
  echo ""
  echo "example: $0 --site master.bitplan.com"
  exit 1
}
 
 
#  
# download the language images to the given site
# activated by options:
#   -s|--site
# 
lang_images () {
  local l_target="$1"
  if [ ! -d $l_target ]
  then
    error "image directory $l_target does not exist"
  fi
  from=http://semantic-mediawiki.org/w/
  for img in images/e/e7/Lang-De.gif images/7/78/Lang-En.gif images/6/61/Lang-Es.gif images/f/f0/Lang-Fr.gif images/9/95/Lang-Ja.gif images/c/cb/Lang-Nl.gif images/3/38/Lang-Ru.gif images/8/85/Lang-Zh-hans.gif images/2/20/Lang-Uk.gif
  do
    imgpath=`echo $img | cut -f1-3 -d/`
    imgname=`echo $img | cut -f4 -d/`
    if [ ! -f $l_target/$img ]
    then
      color_msg $blue "downloading $imgname ..."
      mkdir -p $l_target/$imgpath
      curl -s -o $l_target/$img $from/$img
      chown www-data.www-data $imgpath
    else
      color_msg $green "$imgname already downloaded"
   fi
  done
}

if [ $# -lt 1 ]
then
  usage
fi 
# start of script
# check arguments
while test $# -gt 0
do
  case $1 in
    # -h|--help|usage|show this usage
    -h|--help) 
    usage
    ;;

    # -s|--site|lang_images|download the language images to the given site
    -s|--site) 
      shift
      site=$1
      lang_images "$site"
      ;;
  esac
  shift
done
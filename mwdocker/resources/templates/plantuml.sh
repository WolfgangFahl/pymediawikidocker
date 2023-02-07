#!/bin/bash
# WF 2020-10-22
# invoke plantuml
#  plantuml version to use if not there yet
url=https://sourceforge.net/projects/plantuml/files/1.2023.1/plantuml.1.2023.1.jar/download
# jar file to use
jarPath=/var/www/mediawiki/code/extensions/Diagrams
jar=$jarPath/plantuml.jar


# create a log file
log=/tmp/plantuml.log
debug=true

clearlog() {
  if [ -f $log ]
  then
    rm $log
  fi
}

#
# log the given message
# param 1: msg - the message to log
#
dolog() {
  local l_msg="$1"
  echo "$l_msg" >> $log
}

# remove existing log if any
clearlog
# check if jar is available
if [ ! -f $jar ]
then
   #if not download it
   # allow writing of target path
   chmod g+w $jarPath
   dolog "trying download of $jar " 
   wget $url -O $jar 2>&1 >> $log
   dolog "wget return-code: $?" 
fi
# $cmdArgs = [ "-t$outputFormat", '-output', dirname( $outputFilename ), '--outputFile', $outputFilename ];
for var in "$@"
do
  dolog "param: $var"
  if [ -f $var ]
  then
     dolog "ls -l $var"
     ls -l $var >> $log
	   cat $var >> $log
     b=$(basename $var)
     # create a copy for inspection
     cp -p $var /tmp/$b.bak
  fi
done
while [  "$1" != ""  ]
do
  option=$1
  shift
  # optionally show usage
  case $option in
    -tpng)
      format=$option
      ext=".png"
    ;;
    -tsvg)
      format=$option
      ext=".svg"
    ;;
    -output)
     output=$1
     shift
    ;;
    --outputFile)
      outputFile=$1
      shift
    ;;
  esac
  inputFilename=$option
done
# log run
#/usr/bin/java -Djava.awt.headless=true -jar $jar $@ >> $log 2>&1
# true run
#/usr/bin/java -Djava.awt.headless=true -jar $jar $@
# log run
export GRAPHVIZ_DOT=/usr/bin/dot
dolog "GRAHPVIZ_DOT=$GRAPHVIZ_DOT"
ls -l $GRAPHVIZ_DOT >> $log
echo "/usr/bin/java -Djava.awt.headless=true -jar $jar $format --output $output $inputFilename" >> $log
/usr/bin/java -Djava.awt.headless=true -jar $jar $format --output $output $inputFilename >> $log 2>&1
echo "inputFilename is $inputFilename"  >> $log
bname=$(basename $inputFilename .plantuml)
dname=$(dirname $inputFilename)
plantfile="$dname/$bname$ext"
echo "dirname is $dname basename is $bname ext is $ext -> plantfile=$plantfile"  >> $log
ls -l $plantfile >> $log
echo "outputFile is $outputFile"  >> $log
if [ -f $plantfile ] 
then
  echo "copying $plantfile to $outputFile"  >> $log
  cp -p $plantfile $outputFile
fi
#!/bin/sh

cd ../../
xx=`pwd`
IFS=\

cd /Volumes/App\ Data/Development/DTPO\ Autoload\ Test/Sample\ Files/
for file in *
do
	if [ "$1" == "load" ];
	then
		python $xx/dtpoautoload.py --config_file /Volumes/App\ Data/Development/DTPO\ Autoload\ Test/etc/dtpo_autoload.conf $file
	else
		python $xx/dtpoautoload.py --test_parse  --config_file /Volumes/App\ Data/Development/DTPO\ Autoload\ Test/etc/dtpo_autoload.conf $file
	fi
done

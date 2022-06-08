#!/bin/bash

if [ -d ./data ];
then
	bash setup/get_data.sh
else
	echo 'Making data directory...'
	mkdir data
	bash setup/get_data.sh
fi

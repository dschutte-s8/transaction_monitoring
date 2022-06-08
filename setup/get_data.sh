#!/bin/bash
# Tested on Ubuntu 20.04.4

if [ -d ./data ];
then
	cd ./data
elif [ -d ../data ];
then
	cd ../data
else
	echo 'Unsure where data directory is...'
	exit 0
fi

#########################
# Retrieve zip archives #
#########################

echo 'Retrieving data...'

# Retrieves bank v2.1
# Will do fix later
# wget --output-document 'v2.1-data.zip' 'https://uce75456bd6bda948a1a03ce79cf.dl.dropboxusercontent.com/zip_download_get/BKFYgiOJ_4nqm7xD3aazQhvr-OKAWAQRRDRlf4-r3CjuGSjOh7NV5a1omJ0vwlwIGIXNaOa4c2ihhB-sucEsEkPi7Gd1gjCj7Fta2jvKbUBfDw?_download_id=78517801269199080525709667045716275192616235283599634396798843723&_notify_domain=www.dropbox.com&dl=1'

# Retrieves 10kvertices-1Medges
wget --output-document '10Kvertices-1Medges.7z' 'https://www.dropbox.com/sh/l3grpumqfgbxqak/AADsWllVa5CIbgBMcFXKAFhda/10Kvertices-1Medges.7z?dl=0'

echo 'Data retrieved...'

##################
# Unzip archives #
##################
# unzip v2.1-data.zip

echo 'Unzipping...'

unzip v2.1-data.zip

read -p 'Do you mind if p7zip is installed? [y/n]: ' PERMIT_INSTALL

if [ $PERMIT_INSTALL=='y' ];
then
	sudo apt-get update
	yes y | sudo apt-get install p7zip-full
	7z x 10Kvertices-1Medges.7z

elif [ $PERMIT_INSTALL=='n' ];
then

	echo 'Permission denied, skipping install. You will need to unzip the 7zip file manually.'

else

	echo Invalid input $PERMIT_INSTALL, interrupting execution...
	exit 0

fi

echo 'Unzipping complete...'

# Iteratively unarchive .gz files in v2.1
# Will do later


# Delete zip archives

echo 'Cleaning up...'

rm 10Kvertices-1Medges.7z

echo '[PROCESS COMPLETED]'

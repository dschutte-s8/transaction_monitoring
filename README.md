# Introduction

This is meant to serve as a toolbox or playground for our team to work on a transaction monitoring solution. The hope is that folks will add new tools or techniques that they develop or contribute things that just make the work easier and this will be updated accordingly.


# Setup

## PyGraphviz
Installing pygraphviz first requires installing graphviz before installing pygraphviz via pip.

### Linux
```sudo apt-get install graphviz graphviz-dev```

### MacOS
```brew install graphviz```

## AWS
We will have an AWS environment setup with the datasets pre-loaded into S3 buckets and Neptune setup and ready to go. You will just have to clone the repo and install the packages in the requirements file.

## Local
If you want to experiment with this locally, you will want to run the ```setup.sh``` script in the project root or the ```get_data.sh script``` in the ```setup``` folder first. Currently (06/06/2021) it only installs a graph containing 10K accounts and 1M transactions.


# Overview

## Intro

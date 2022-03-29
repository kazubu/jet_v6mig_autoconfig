#!/bin/sh

jet-pkg-gen.py -i ./v6mig_autoconfig.json -p ./src

cd src
mk-i386,bsdx v6mig_autoconfig
#mk-amd64,bsdx v6mig_autoconfig

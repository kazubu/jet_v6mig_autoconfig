#!/bin/sh

jet-pkg-gen.py -i ./v6mig_autoconfig.json -p ./src

cd src
export PKG_VERSION=0.0.3
PYTHON_MOD_INSTALLDIR=opt/lib/python3.7/site-packages PYTHON_MAJOR_VERSION=3 mk-i386,bsdx v6mig_autoconfig
#mk-amd64,bsdx v6mig_autoconfig

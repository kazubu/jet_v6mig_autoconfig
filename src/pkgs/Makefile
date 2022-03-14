#
# $Id$
#
# Makefile - packaging make file.
# All the interesting stuff happens in ${SB_BACKING_SB}/src/pkgs/Makefile.
#
# Copyright (c) 2015 Juniper Networks, Inc.
# All rights reserved.
#
PKG_DIST_ARGS = \
	-b ${SRCTOP}/pkgs/pkg-dist.bom

# Dummy rule for ship-packages
# we use ship-jet-pkgs target to ship.
ship-packages:
	@echo

.include "${SB_BACKING_SB}/src/build/mk/pkg/top.mk"

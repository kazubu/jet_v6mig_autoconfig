#
# $Id: $
#
# Copyright (c) 2015, Juniper Networks, Inc.
# All rights reserved.
#

# This is the top-level makefile for the juniper jet examples that are
# shipped with the junos-jet.
#
# sbin -- contains the example application(s)
# lib  -- contains the ddl and odl libraries for the example app(s)
# etc  -- builds the certificate chain for the example package(s)
.include <JET-VERSION>
.if ${clean* destroy* checkout* update* check-update *-jobs:${M_L_TARGETS}} != "" || !exists(${.CURDIR}/pkgs/Makefile)
.include "${SB_BACKING_SB}/src/build/Makefile"
.if !target(${.TARGETS})
.include "pkgs/Makefile"
.endif
.else
.include "pkgs/Makefile"
.endif


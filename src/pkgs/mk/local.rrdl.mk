#
# $Id$
#
# Copyright (c) 2015, Juniper Networks, Inc.
# All rights reserved.
#

.if defined(PROVIDER_POLICIES)
.for p in ${PROVIDER_POLICIES}
CRRDL_PATH += ${LIBRRDL:H:H:S,${OBJTOP_JUNOS},${SRCTOP},}/input/policy/${p}
.endfor
CRRDL_PATH += ${LIBRRDL:H:H:S,${OBJTOP_JUNOS},${HOST_OBJTOP_JUNOS},}/input
.endif

.include "${SB_BACKING_SB}/src/build/mk/jnx.rrdl.mk"


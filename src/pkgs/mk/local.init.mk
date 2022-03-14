# $Id$
#
# Copyright (c) 2015, Juniper Networks, Inc.
# All rights reserved.
#

JUNOS_JET_BUILD_ENV = yes

NEED_IMPLICIT_LDADD ?= yes

# we define this symbol to make sure we get the right includes
CFLAGS += -D__JUNOS_SDK__ -D__JUNOS_JET__

CFLAGS += \
	-I${SRCTOP}/include \
	-I${SRCTOP_BSD}/sys/posix4 \
	-I${SRCTOP_BSD}/include \
	-I${OBJTOP_BSD}/include

HOST_CFLAGS += -D__JUNOS_SDK__ -D__JUNOS_JET__

.include <provider-prefix.mk>
JUNOS_JET_INSTALLDIR ?= /var/db/scripts/jet

.if defined(PROG)
.if ${TARGET_OS} == "bsd6"
# system link flags for legacy build 
# Staged libs in backing sb
LDFLAGS += -L${PUBLISH_PREFIX}/${MACHINE}/stage/usr/lib
.endif

# link flags for staged libs path built in dev sandbox
LDFLAGS += -L${_OBJTOP}/usr/lib
.endif

.if defined(LIB)
# Stage the libs built in dev sandbox
STAGE_LIBDIR= ${_OBJTOP}/usr/lib
SHLIB_DEBUG_LINK= ${STAGE_LIBDIR}/lib${LIB}.so
.endif

# Pick up the Juniper init
.include "${SYS_MK_DIR}/bsd.init.mk"

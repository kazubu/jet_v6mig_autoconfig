#
# $Id:$
#
# Copyright (c) 2015-2020, Juniper Networks, Inc.
# All rights reserved.
#

.MAIN: all

# HOST_OBJTOP_BUILD not valid, and we need to reach into the SB_BACKING_SB
.PATH: ${HOST_OBJTOP_JUNOS:H}/build/certs
all: certs.pem
certs.pem: ${SIGCERT} jet-certs.pem
	echo SIGCERT is ${SIGCERT}
	cat ${.ALLSRC:M*.pem} > $@

.include "${SYS_MK_DIR}/pkg/jnx.setup.mk"

clean:
	rm -f certs.pem

cleandepend:


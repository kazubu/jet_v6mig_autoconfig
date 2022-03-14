#
# $Id$
#
# Copyright (c) 2015, Juniper Networks, Inc.
# All rights reserved.
#

.ifndef __provider_prefix_mk__
__provider_prefix_mk__ = 1

.if ${NOSIG} != "yes"
PROVIDER_PREFIX != ${EXTRACT_PROV_PREFIX} ${SIGCERT}
.else
PROVIDER_PREFIX=
.endif

.endif


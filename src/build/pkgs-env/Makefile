all bootstrap: export-host-utils-env

PKGSCRIPTS_DIRS ?= \
	${XDL_CLASSES:O:u:tu:@X@${SRCTOP_${X}}/package-scripts@} \
	${SRCTOP_JUNOS}/package-scripts \
	${SRCTOP}/pkgs/package-scripts \
	${SRCTOP_ESP}/package-scripts

.include <jnx.hosttools.mk>
.include <pkg/jnx.setup.mk>
.include <pkg/pathnames.mk>

PKGDIR = ${OBJTOP}/pkgs/rootdir/packages

.include <pkg/pkgutils-env.mk>

UPDATE_DEPENDFILE = no

.if !make(bootstrap)
all:    stage_files

${PKGDIR}: .NOMETA
	mkdir -p $@

# certs are must in signed mode only.
.if ${NOSIG} != "yes"
# every package depends on this
STAGE_FILES = ${SIGS:S,sig,certs,:@x@${CERTS_PEM:H}/$x.pem@}
.else
STAGE_FILES=
.endif

STAGE_DIR =  ${PKGDIR}
stage_files: ${STAGE_DIR}

.include <meta.stage.mk>
.endif


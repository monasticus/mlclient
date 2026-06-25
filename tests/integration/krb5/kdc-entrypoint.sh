#!/bin/bash
# Bring up a self-contained MIT Kerberos KDC for the integration suite.
#
# It creates the realm, the MarkLogic service principal (HTTP/localhost) and a
# client principal, then exports two keytabs onto shared volumes: services.keytab
# for the MarkLogic container and client.keytab for the test host's kinit. A
# readiness marker is written last so dependants only start once tickets can be
# issued.
set -euo pipefail

REALM="${KRB5_REALM:-MLCLIENT.LOCAL}"
KADMIN_PASS="${KRB5_KADMIN_PASSWORD:-kadminpass}"
SERVICE_PRINCIPAL="HTTP/localhost@${REALM}"
CLIENT_PRINCIPAL="${KRB5_CLIENT_PRINCIPAL:-mlclient}@${REALM}"

SERVICE_KEYTAB="${KRB5_SERVICE_KEYTAB:-/service-keytab/services.keytab}"
CLIENT_KEYTAB="${KRB5_CLIENT_KEYTAB:-/client-keytab/client.keytab}"
READY_MARKER="$(dirname "${CLIENT_KEYTAB}")/.kdc-ready"

rm -f "${READY_MARKER}"

# A fresh realm database on every start keeps the rig stateless and idempotent.
kdb5_util create -r "${REALM}" -s -P "${KADMIN_PASS}"

kadmin.local -q "addprinc -randkey ${SERVICE_PRINCIPAL}"
kadmin.local -q "addprinc -randkey ${CLIENT_PRINCIPAL}"

# Keytabs carry every key the principal has; the permitted enctypes in
# krb5.conf govern what the tickets actually negotiate.
rm -f "${SERVICE_KEYTAB}" "${CLIENT_KEYTAB}"
kadmin.local -q "ktadd -k ${SERVICE_KEYTAB} ${SERVICE_PRINCIPAL}"
kadmin.local -q "ktadd -k ${CLIENT_KEYTAB} ${CLIENT_PRINCIPAL}"

# The keytabs cross container and host boundaries via bind mounts, so they must
# be world-readable; this is a disposable test realm with no real secrets.
chmod 0644 "${SERVICE_KEYTAB}" "${CLIENT_KEYTAB}"

touch "${READY_MARKER}"

exec krb5kdc -n

#!/bin/bash
# Start MarkLogic, provision the connection/auth matrix once it is ready, then
# stay in the foreground for the lifetime of the container.
#
# The stock image entrypoint initialises MarkLogic and ends in `tail -f
# /dev/null`. We run it in the background, provision over the Management API,
# and then wait on it so the container keeps running and signals propagate.
set -euo pipefail

CERTS_DIR="${MLCLIENT_IT_CERTS_DIR:-/certs}"
SERVICE_KEYTAB="${MLCLIENT_IT_SERVICE_KEYTAB:-/service-keytab/services.keytab}"

# Clear any marker left in a bind-mounted volume by a previous run so the
# healthcheck only passes once this run has finished provisioning.
rm -f "${CERTS_DIR}/.provisioned"

# MarkLogic reads its Kerberos keytab from the data directory; the KDC writes it
# to a shared volume. Copy it into place before the server starts so the service
# principal is available for the kerberos-ticket app server.
if [ -f "${SERVICE_KEYTAB}" ]; then
    cp "${SERVICE_KEYTAB}" /var/opt/MarkLogic/services.keytab
fi

/usr/local/bin/start-marklogic.sh &
marklogic_pid=$!

# Keep MarkLogic running even if provisioning fails, so the container stays up
# for log inspection. The readiness marker is only written on success, so the
# healthcheck (and therefore the test run) gates on a fully provisioned matrix.
if python3 -m provision.provision --host localhost --certs-dir "${CERTS_DIR}"; then
    chmod -R a+rX "${CERTS_DIR}"
    touch "${CERTS_DIR}/.provisioned"
else
    echo "Provisioning failed; MarkLogic left running for inspection." >&2
fi

wait "${marklogic_pid}"

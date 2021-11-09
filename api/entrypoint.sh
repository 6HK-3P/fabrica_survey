#!/bin/sh

# initial

set -o errexit
set -o nounset

# wait for postgres

postgres_ready() {
python << END
import sys
import psycopg2

try:
    psycopg2.connect("host='${DATABASE_HOST}' \
                      port='${DATABASE_PORT}' \
                      dbname='${DATABASE_NAME}' \
                      user='${DATABASE_USER}' \
                      password='${DATABASE_PASSWORD}'")
except psycopg2.OperationalError:
    sys.exit(-1)
sys.exit(0)
END
}
until postgres_ready; do
  >&2 echo 'Waiting for PostgreSQL to become available...'
  sleep 1
done
>&2 echo 'PostgreSQL is available'


# everything is ready

exec "$@"

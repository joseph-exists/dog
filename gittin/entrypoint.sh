#!/bin/sh
set -eu

APP_INI=${GOGS_CUSTOM_CONF:-/data/gogs/conf/app.ini}
APP_INI_DIR=$(dirname "$APP_INI")
REPO_ROOT=${GITTIN_REPO_ROOT:-/data/git}
APP_DATA_PATH=${GITTIN_APP_DATA_PATH:-/data/gogs/data}
LOG_PATH=${GITTIN_LOG_PATH:-/data/gogs/log}
SSH_ROOT_PATH=${GITTIN_SSH_ROOT_PATH:-/data/ssh}
DB_PATH=${GITTIN_DB_PATH:-/data/gogs/data/gogs.db}
DOMAIN=${GITTIN_DOMAIN:-localhost}
HTTP_PORT=${GITTIN_HTTP_PORT:-3000}
SSH_PORT=${GITTIN_SSH_PORT:-2222}
SSH_LISTEN_PORT=${GITTIN_SSH_LISTEN_PORT:-2222}
EXTERNAL_URL=${GITTIN_EXTERNAL_URL:-http://localhost:${HTTP_PORT}/}
RUN_MODE=${GITTIN_RUN_MODE:-prod}
DISABLE_REGISTRATION=${GITTIN_DISABLE_REGISTRATION:-false}
REQUIRE_SIGNIN_VIEW=${GITTIN_REQUIRE_SIGNIN_VIEW:-false}
ENABLE_REGISTRATION_CAPTCHA=${GITTIN_ENABLE_REGISTRATION_CAPTCHA:-false}
INSTALL_LOCK=${GITTIN_INSTALL_LOCK:-false}

mkdir -p "$APP_INI_DIR" "$REPO_ROOT" "$APP_DATA_PATH" "$LOG_PATH" "$SSH_ROOT_PATH"

set_ini_value() {
  section="$1"
  key="$2"
  value="$3"
  tmp_file=$(mktemp)

  awk -v section="$section" -v key="$key" -v value="$value" '
    BEGIN {
      in_section = 0
      section_found = 0
      key_written = 0
    }

    $0 == "[" section "]" {
      if (in_section && !key_written) {
        print key " = " value
        key_written = 1
      }
      print
      in_section = 1
      section_found = 1
      next
    }

    in_section && /^\[/ {
      if (!key_written) {
        print key " = " value
        key_written = 1
      }
      in_section = 0
    }

    {
      if (in_section && $0 ~ "^[[:space:]]*" key "[[:space:]]*=") {
        if (!key_written) {
          print key " = " value
          key_written = 1
        }
        next
      }
      print
    }

    END {
      if (in_section && !key_written) {
        print key " = " value
      } else if (!section_found) {
        print ""
        print "[" section "]"
        print key " = " value
      }
    }
  ' "$APP_INI" > "$tmp_file"

  mv "$tmp_file" "$APP_INI"
}

if [ ! -f "$APP_INI" ]; then
  cat > "$APP_INI" <<EOF
RUN_USER = git
RUN_MODE = ${RUN_MODE}

[server]
EXTERNAL_URL = ${EXTERNAL_URL}
DOMAIN = ${DOMAIN}
PROTOCOL = http
HTTP_ADDR = 0.0.0.0
HTTP_PORT = ${HTTP_PORT}
APP_DATA_PATH = ${APP_DATA_PATH}
SSH_ROOT_PATH = ${SSH_ROOT_PATH}
DISABLE_SSH = false
SSH_DOMAIN = ${DOMAIN}
SSH_PORT = ${SSH_PORT}
START_SSH_SERVER = true
SSH_LISTEN_HOST = 0.0.0.0
SSH_LISTEN_PORT = ${SSH_LISTEN_PORT}

[repository]
ROOT = ${REPO_ROOT}
DEFAULT_BRANCH = main
DISABLE_HTTP_GIT = false

[database]
TYPE = sqlite3
PATH = ${DB_PATH}

[security]
INSTALL_LOCK = ${INSTALL_LOCK}
COOKIE_SECURE = false

[auth]
REQUIRE_SIGNIN_VIEW = ${REQUIRE_SIGNIN_VIEW}
DISABLE_REGISTRATION = ${DISABLE_REGISTRATION}
ENABLE_REGISTRATION_CAPTCHA = ${ENABLE_REGISTRATION_CAPTCHA}
EOF
  echo "[gittin] Wrote initial Gogs config to ${APP_INI}"
else
  echo "[gittin] Reusing existing Gogs config at ${APP_INI}"
fi

# Keep stateful paths on mounted storage even if the web installer wrote
# image-local defaults such as "data/gogs.db" or "/app/gogs/log".
set_ini_value "server" "APP_DATA_PATH" "$APP_DATA_PATH"
set_ini_value "server" "SSH_ROOT_PATH" "$SSH_ROOT_PATH"
set_ini_value "repository" "ROOT" "$REPO_ROOT"
set_ini_value "database" "PATH" "$DB_PATH"
set_ini_value "log" "ROOT_PATH" "$LOG_PATH"

echo "[gittin] Repo root: ${REPO_ROOT}"

if command -v gogs >/dev/null 2>&1; then
  GOGS_BIN=$(command -v gogs)
elif [ -x /app/gogs/gogs ]; then
  GOGS_BIN=/app/gogs/gogs
elif [ -x /opt/gogs/gogs ]; then
  GOGS_BIN=/opt/gogs/gogs
elif [ -x /usr/local/bin/gogs ]; then
  GOGS_BIN=/usr/local/bin/gogs
else
  echo "[gittin] Could not locate the Gogs binary" >&2
  exit 127
fi

exec "$GOGS_BIN" web

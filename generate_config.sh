#!/usr/bin/env bash
set -euo pipefail

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

: "${API_URL:?Set API_URL in the environment or in .env}"
sed "s|__API_URL__|$API_URL|g" \
  pages/static/js/config.template.js > pages/static/js/config.js
echo "config.js generated with API_URL=$API_URL"

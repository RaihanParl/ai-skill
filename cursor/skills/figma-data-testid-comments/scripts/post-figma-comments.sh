#!/usr/bin/env bash
# Post Figma Comments for QA data-testid pins.
#
# Usage:
#   FIGMA_TOKEN=figd_... ./post-figma-comments.sh <file_key> < comments.tsv
#
# TSV columns (tab-separated):
#   node_id  offset_x  offset_y  message
#
# message may be either:
#   button-apply-filter-overspeed
#   QA data-testid: button-apply-filter-overspeed
#
# Requires: curl, jq

set -euo pipefail

FILE_KEY="${1:-}"
if [[ -z "${FILE_KEY}" ]]; then
  echo "usage: FIGMA_TOKEN=... $0 <file_key> < comments.tsv" >&2
  exit 2
fi

if [[ -z "${FIGMA_TOKEN:-}" ]]; then
  echo "FIGMA_TOKEN is required (Personal Access Token with file_comments:write)" >&2
  exit 2
fi

API="https://api.figma.com/v1/files/${FILE_KEY}/comments"
ok=0
fail=0

while IFS=$'\t' read -r node_id ox oy message || [[ -n "${node_id:-}" ]]; do
  # skip blank / comment lines
  [[ -z "${node_id:-}" ]] && continue
  [[ "${node_id}" =~ ^# ]] && continue

  ox="${ox:-0}"
  oy="${oy:-0}"
  message="${message:-}"

  if [[ -z "${message}" ]]; then
    echo "SKIP ${node_id}: empty message" >&2
    fail=$((fail + 1))
    continue
  fi

  if [[ "${message}" != QA\ data-testid:* ]]; then
    message="QA data-testid: ${message}"
  fi

  body=$(jq -n \
    --arg msg "${message}" \
    --arg nid "${node_id}" \
    --argjson ox "${ox}" \
    --argjson oy "${oy}" \
    '{message:$msg, client_meta:{node_id:$nid, node_offset:{x:$ox, y:$oy}}}')

  code=$(curl -sS -o /tmp/figma-comment-post.json -w "%{http_code}" \
    -X POST \
    -H "X-FIGMA-TOKEN: ${FIGMA_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "${body}" \
    "${API}")

  if [[ "${code}" == "200" ]]; then
    ok=$((ok + 1))
    echo "OK  ${node_id} (${ox},${oy}) -> ${message}"
  else
    fail=$((fail + 1))
    echo "FAIL ${code} ${node_id} -> $(head -c 240 /tmp/figma-comment-post.json)" >&2
  fi

  sleep 0.35
done

echo "---"
echo "ok=${ok} fail=${fail}"
[[ "${fail}" -eq 0 ]]

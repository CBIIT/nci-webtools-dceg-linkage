#!/usr/bin/env bash
# runtime_limit_test.sh
#
# Submits sequential LDproxy requests one at a time (waits for each response
# before sending the next) until the runtime-limit block fires or MAX_CALLS
# is reached.
#
# Usage:
#   ./tests/load/runtime_limit_test.sh
#   TOKEN=<your_token> ./tests/load/runtime_limit_test.sh
#   TOKEN=abc MAX_CALLS=100 BASE_URL=https://ldlink-dev.nih.gov ./tests/load/runtime_limit_test.sh
# curl -k -X GET 'https://ldlink-dev.nih.gov/LDlinkRest/ldproxy?var=rs3&pop=MXL&r2_d=r2&window=500000&genome_build=grch37&token=3da5c07d160b'

set -euo pipefail

TOKEN="${TOKEN:-3da5c07d160b}"
BASE_URL="${BASE_URL:-https://ldlink-dev.nih.gov}"
MAX_CALLS="${MAX_CALLS:-130}"
ENDPOINT="/LDlinkRest/ldproxy?var=rs3&pop=MXL&r2_d=r2&window=500000&genome_build=grch37&token=${TOKEN}"

BLOCKED_PATTERN="temporarily blocked"
OK_COUNT=0
TOTAL_WALL_SECS=0

echo "=============================================="
echo " Runtime-limit sequential test"
echo " Target  : ${BASE_URL}"
echo " Max     : ${MAX_CALLS} calls"
echo " Token   : ${TOKEN}"
echo " Started : $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================="
echo ""

for (( i=1; i<=MAX_CALLS; i++ )); do
    echo "[$(date '+%H:%M:%S')] Submitting call #${i} of ${MAX_CALLS} ..."
    CALL_START=$(date +%s)

    # Append HTTP status after a known separator so we can split body vs status.
    RESPONSE=$(curl -sk \
        -w "\n---HTTP_STATUS---%{http_code}---" \
        -X GET "${BASE_URL}${ENDPOINT}" 2>&1)

    CALL_END=$(date +%s)
    WALL_SECS=$(( CALL_END - CALL_START ))
    TOTAL_WALL_SECS=$(( TOTAL_WALL_SECS + WALL_SECS ))

    BODY=$(echo "$RESPONSE" | grep -v -- '---HTTP_STATUS---' || true)
    HTTP_STATUS=$(echo "$RESPONSE" | grep -o -- '---HTTP_STATUS---[0-9]*---' | grep -o '[0-9]*' || echo "000")

    TIMESTAMP=$(date '+%H:%M:%S')

    # The block is returned as HTTP 200 with a JSON error body, so we must
    # inspect the body rather than the HTTP status code.
    if echo "$BODY" | grep -qi "$BLOCKED_PATTERN"; then
        echo "[$TIMESTAMP] Call #${i}  HTTP ${HTTP_STATUS}  wall ${WALL_SECS}s  *** BLOCKED ***"
        echo ""
        echo "Block message:"
        echo "$BODY" | grep -o '"error"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/"error"[[:space:]]*:[[:space:]]*"//;s/"$//' || echo "$BODY"
        echo ""
        echo "----------------------------------------------"
        echo " RESULT          : BLOCKED"
        echo " Blocked on call : #${i} of ${MAX_CALLS}"
        echo " Blocked URL     : ${BASE_URL}${ENDPOINT}"
        echo " Resume from     : call #$(( i + 1 )) next run"
        echo " Successful calls: ${OK_COUNT}"
        echo " Wall time total : ${TOTAL_WALL_SECS}s"
        echo " Finished        : $(date '+%Y-%m-%d %H:%M:%S')"
        echo " Runtime limit test: PASS (block fired as expected)"
        echo "----------------------------------------------"
        exit 0
    fi

    # Any other JSON error body — log it and keep going (transient errors).
    if echo "$BODY" | grep -qi '"error"'; then
        ERROR_MSG=$(echo "$BODY" | grep -o '"error"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/"error"[[:space:]]*:[[:space:]]*"//;s/"$//' || echo "$BODY")
        echo "[$TIMESTAMP] Call #${i}  HTTP ${HTTP_STATUS}  wall ${WALL_SECS}s  ERROR: ${ERROR_MSG}"
        continue
    fi

    OK_COUNT=$(( OK_COUNT + 1 ))
    echo "[$TIMESTAMP] Call #${i}  HTTP ${HTTP_STATUS}  wall ${WALL_SECS}s  OK (#${OK_COUNT} success)"
done

echo ""
echo "----------------------------------------------"
echo " RESULT          : MAX_CALLS (${MAX_CALLS}) reached without a block"
echo " Successful calls: ${OK_COUNT}"
echo " Wall time total : ${TOTAL_WALL_SECS}s"
echo " Finished        : $(date '+%Y-%m-%d %H:%M:%S')"
echo " Runtime limit test: FAIL — block did not fire"
echo " Tip: raise MAX_CALLS or lower RUNTIME_LIMIT_MS_24H"
echo "----------------------------------------------"
exit 1

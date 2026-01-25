#!/bin/bash
# Integration test script for hab CLI using empty-hass
# Usage: ./run_integration_test.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
HAB="$PROJECT_DIR/hab"
CONFIG_DIR=$(mktemp -d)
EMPTY_HASS_PID=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test token from empty-hass
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIyZWZkZGJjZmY0MzQ0NGRlYmUyMDhkNDUyM2RlNTIwMSIsImlhdCI6MTc2OTI4MjkyNiwiZXhwIjoyMDg0NjQyOTI2fQ.ZYSmLdcv5EfGCXrwO2Nd6bxHrxxU-7ieuE0ySwurU9A"
URL="http://localhost:8124"

# Counters
PASSED=0
FAILED=0

cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    if [ -n "$EMPTY_HASS_PID" ]; then
        kill $EMPTY_HASS_PID 2>/dev/null || true
        wait $EMPTY_HASS_PID 2>/dev/null || true
    fi
    rm -rf "$CONFIG_DIR"
    echo -e "${YELLOW}Done.${NC}"
}

trap cleanup EXIT

log_test() {
    echo -e "\n${YELLOW}TEST: $1${NC}"
}

pass() {
    echo -e "${GREEN}PASS${NC}: $1"
    PASSED=$((PASSED + 1))
}

fail() {
    echo -e "${RED}FAIL${NC}: $1"
    FAILED=$((FAILED + 1))
}

run_hab() {
    "$HAB" --config "$CONFIG_DIR" "$@"
}

wait_for_hass() {
    echo "Waiting for Home Assistant to be ready..."
    for i in {1..60}; do
        if curl -s -H "Authorization: Bearer $TOKEN" "$URL/api/" > /dev/null 2>&1; then
            echo "Home Assistant is ready!"
            return 0
        fi
        sleep 2
    done
    echo "Home Assistant did not become ready in time"
    return 1
}

# Build the CLI
echo -e "${YELLOW}Building hab CLI...${NC}"
cd "$PROJECT_DIR"
go build -o hab .
echo "Built: $HAB"

# Start empty-hass
echo -e "\n${YELLOW}Starting empty-hass...${NC}"
uvx --from git+https://github.com/balloob/empty-hass empty-hass --port 8124 > /dev/null 2>&1 &
EMPTY_HASS_PID=$!
echo "Started empty-hass with PID: $EMPTY_HASS_PID"

# Wait for it to be ready
wait_for_hass

echo -e "\n${YELLOW}Running tests...${NC}"
echo "Config directory: $CONFIG_DIR"

# Test: auth login
log_test "auth login"
OUTPUT=$(run_hab auth login --token --url "$URL" --access-token "$TOKEN")
if echo "$OUTPUT" | jq -e '.success == true' > /dev/null 2>&1; then
    pass "auth login"
else
    fail "auth login: $OUTPUT"
fi

# Test: auth status
log_test "auth status"
OUTPUT=$(run_hab auth status )
if echo "$OUTPUT" | jq -e '.success == true and .data.authenticated == true' > /dev/null 2>&1; then
    pass "auth status"
else
    fail "auth status: $OUTPUT"
fi

# Test: system info
log_test "system info"
OUTPUT=$(run_hab system info )
if echo "$OUTPUT" | jq -e '.success == true and .data.version != null' > /dev/null 2>&1; then
    VERSION=$(echo "$OUTPUT" | jq -r '.data.version')
    pass "system info (version: $VERSION)"
else
    fail "system info: $OUTPUT"
fi

# Test: system health
log_test "system health"
OUTPUT=$(run_hab system health )
if echo "$OUTPUT" | jq -e '.success == true' > /dev/null 2>&1; then
    pass "system health"
else
    fail "system health: $OUTPUT"
fi

# Test: entity list
log_test "entity list"
OUTPUT=$(run_hab entity list )
if echo "$OUTPUT" | jq -e '.success == true' > /dev/null 2>&1; then
    COUNT=$(echo "$OUTPUT" | jq '.data | if . == null then 0 else length end')
    pass "entity list ($COUNT entities)"
else
    fail "entity list: $OUTPUT"
fi

# Test: action list
log_test "action list"
OUTPUT=$(run_hab action list )
if echo "$OUTPUT" | jq -e '.success == true and (.data | length) > 0' > /dev/null 2>&1; then
    COUNT=$(echo "$OUTPUT" | jq '.data | length')
    pass "action list ($COUNT actions)"
else
    fail "action list: $OUTPUT"
fi

# Test: area CRUD
log_test "area create"
AREA_NAME="Test Area $(date +%s)"
OUTPUT=$(run_hab area create "$AREA_NAME" )
if echo "$OUTPUT" | jq -e '.success == true and .data.area_id != null' > /dev/null 2>&1; then
    AREA_ID=$(echo "$OUTPUT" | jq -r '.data.area_id')
    pass "area create (id: $AREA_ID)"

    log_test "area list"
    OUTPUT=$(run_hab area list )
    if echo "$OUTPUT" | jq -e ".success == true and (.data | map(select(.area_id == \"$AREA_ID\")) | length) > 0" > /dev/null 2>&1; then
        pass "area list (found created area)"
    else
        fail "area list: created area not found"
    fi

    log_test "area update"
    OUTPUT=$(run_hab area update "$AREA_ID" --name "$AREA_NAME Updated" )
    if echo "$OUTPUT" | jq -e '.success == true' > /dev/null 2>&1; then
        pass "area update"
    else
        fail "area update: $OUTPUT"
    fi

    log_test "area delete"
    OUTPUT=$(run_hab area delete "$AREA_ID" --force )
    if echo "$OUTPUT" | jq -e '.success == true' > /dev/null 2>&1; then
        pass "area delete"
    else
        fail "area delete: $OUTPUT"
    fi
else
    fail "area create: $OUTPUT"
fi

# Test: floor CRUD
log_test "floor create"
FLOOR_NAME="Test Floor $(date +%s)"
OUTPUT=$(run_hab floor create "$FLOOR_NAME" --level 1 )
if echo "$OUTPUT" | jq -e '.success == true and .data.floor_id != null' > /dev/null 2>&1; then
    FLOOR_ID=$(echo "$OUTPUT" | jq -r '.data.floor_id')
    pass "floor create (id: $FLOOR_ID)"

    log_test "floor delete"
    OUTPUT=$(run_hab floor delete "$FLOOR_ID" --force )
    if echo "$OUTPUT" | jq -e '.success == true' > /dev/null 2>&1; then
        pass "floor delete"
    else
        fail "floor delete: $OUTPUT"
    fi
else
    fail "floor create: $OUTPUT"
fi

# Test: label CRUD
log_test "label create"
LABEL_NAME="Test Label $(date +%s)"
OUTPUT=$(run_hab label create "$LABEL_NAME" --color red )
if echo "$OUTPUT" | jq -e '.success == true and .data.label_id != null' > /dev/null 2>&1; then
    LABEL_ID=$(echo "$OUTPUT" | jq -r '.data.label_id')
    pass "label create (id: $LABEL_ID)"

    log_test "label delete"
    OUTPUT=$(run_hab label delete "$LABEL_ID" --force )
    if echo "$OUTPUT" | jq -e '.success == true' > /dev/null 2>&1; then
        pass "label delete"
    else
        fail "label delete: $OUTPUT"
    fi
else
    fail "label create: $OUTPUT"
fi

# Test: --text output
log_test "text output mode"
OUTPUT=$(run_hab --text system info )
if ! echo "$OUTPUT" | jq . > /dev/null 2>&1; then
    # Not valid JSON, which is what we expect for text mode
    if echo "$OUTPUT" | grep -qi "version"; then
        pass "text output mode"
    else
        fail "text output mode: expected version info"
    fi
else
    fail "text output mode: got JSON instead of text"
fi

# Test: auth logout
log_test "auth logout"
OUTPUT=$(run_hab auth logout )
if echo "$OUTPUT" | jq -e '.success == true' > /dev/null 2>&1; then
    pass "auth logout"
else
    fail "auth logout: $OUTPUT"
fi

# Test: auth status after logout
log_test "auth status after logout"
OUTPUT=$(run_hab auth status )
if echo "$OUTPUT" | jq -e '.success == true and .data.authenticated == false' > /dev/null 2>&1; then
    pass "auth status after logout"
else
    fail "auth status after logout: $OUTPUT"
fi

# Summary
echo -e "\n${YELLOW}========================================${NC}"
echo -e "${YELLOW}Test Summary${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}Some tests failed.${NC}"
    exit 1
fi

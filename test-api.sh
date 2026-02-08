#!/bin/bash

# Test script for Service Manager Dashboard
# Tests backend API endpoints

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_URL="${1:-http://localhost:8080}"
TESTS_PASSED=0
TESTS_FAILED=0

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Service Manager Dashboard - API Tests${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Testing backend: $BASE_URL"
echo ""

# Function to test endpoint
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    
    echo -n "Testing: $name ... "
    
    if [ -z "$data" ]; then
        response=$(curl -s -X $method "$BASE_URL$endpoint" -H "Content-Type: application/json")
    else
        response=$(curl -s -X $method "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    if [ -n "$response" ] && echo "$response" | grep -q '"'; then
        echo -e "${GREEN}✓${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC}"
        echo "  Response: $response"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Function to test status code
test_status_code() {
    local name=$1
    local method=$2
    local endpoint=$3
    local expected_code=$4
    local data=$5
    
    echo -n "Testing: $name ... "
    
    if [ -z "$data" ]; then
        status=$(curl -s -o /dev/null -w "%{http_code}" -X $method "$BASE_URL$endpoint")
    else
        status=$(curl -s -o /dev/null -w "%{http_code}" -X $method "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    if [ "$status" = "$expected_code" ]; then
        echo -e "${GREEN}✓ ($status)${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ (got $status, expected $expected_code)${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
max_attempts=10
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s "$BASE_URL/api/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Backend is ready"
        echo ""
        break
    fi
    attempt=$((attempt + 1))
    if [ $attempt -lt $max_attempts ]; then
        echo -n "."
        sleep 1
    fi
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}✗${NC} Backend is not responding"
    echo "Make sure the backend is running on $BASE_URL"
    exit 1
fi

# ==================== Test Health Check ====================
echo -e "${BLUE}Health & Status Tests${NC}"
test_status_code "Health Check" "GET" "/api/health" "200"

# ==================== Test Status Endpoint ====================
echo ""
echo -e "${BLUE}Status Endpoint Tests${NC}"
test_status_code "Get Status" "GET" "/api/status" "200"

# ==================== Test Control Endpoint ====================
echo ""
echo -e "${BLUE}Control Endpoint Tests${NC}"
test_status_code "Start Service (invalid)" "POST" "/api/control" "200" '{"action":"start"}'

# ==================== Test Logs Endpoint ====================
echo ""
echo -e "${BLUE}Logs Endpoint Tests${NC}"
test_status_code "Get Logs" "GET" "/api/logs?service=platform" "200"
test_status_code "Get Logs with Search" "GET" "/api/logs?service=platform&search=INFO" "200"
test_status_code "Get Limited Logs" "GET" "/api/logs?service=platform&lines=50" "200"

# ==================== Test Download Endpoint ====================
echo ""
echo -e "${BLUE}Download Endpoint Tests${NC}"
test_status_code "Download Platform Logs" "GET" "/api/logs/download?service=platform" "200"

# ==================== Summary ====================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  ${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "  ${RED}Failed: $TESTS_FAILED${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}All tests passed! ✓${NC}"
    echo ""
    echo "You can now access the dashboard:"
    echo "  Frontend: http://localhost:5173"
    echo "  Backend API: $BASE_URL"
    echo "  API Docs: $BASE_URL/api/docs"
    echo ""
    exit 0
else
    echo ""
    echo -e "${RED}Some tests failed. Please check the backend logs.${NC}"
    echo ""
    exit 1
fi

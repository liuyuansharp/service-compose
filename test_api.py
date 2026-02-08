#!/usr/bin/env python3
"""
Service Manager Dashboard - API Test Suite
Tests all backend endpoints
"""

import requests
import json
import sys
from typing import Tuple, Dict, Any
from datetime import datetime

# ANSI Color codes
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

class APITester:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip('/')
        self.tests_passed = 0
        self.tests_failed = 0
        self.session = requests.Session()
        
    def print_header(self, text: str):
        """Print a formatted header"""
        print(f"\n{BLUE}{'═' * 50}{NC}")
        print(f"{BLUE}  {text}{NC}")
        print(f"{BLUE}{'═' * 50}{NC}\n")
    
    def print_test(self, name: str, result: bool, details: str = ""):
        """Print test result"""
        if result:
            print(f"  {GREEN}✓{NC} {name}")
            self.tests_passed += 1
        else:
            print(f"  {RED}✗{NC} {name}")
            if details:
                print(f"    {details}")
            self.tests_failed += 1
    
    def test_endpoint(self, name: str, method: str, endpoint: str, 
                     data: Dict = None, expected_status: int = 200) -> bool:
        """Test a single endpoint"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method == "GET":
                response = self.session.get(url)
            elif method == "POST":
                response = self.session.post(url, json=data)
            else:
                return False
            
            success = response.status_code == expected_status
            
            if success:
                # Try to parse JSON response
                try:
                    response.json()
                except:
                    pass  # Not JSON, that's okay
            
            self.print_test(name, success, 
                          f"Status: {response.status_code} (expected {expected_status})")
            return success
            
        except requests.exceptions.ConnectionError:
            self.print_test(name, False, "Connection refused - backend not running?")
            return False
        except Exception as e:
            self.print_test(name, False, str(e))
            return False
    
    def wait_for_backend(self, timeout: int = 30) -> bool:
        """Wait for backend to be ready"""
        print("Waiting for backend to be ready...")
        
        for i in range(timeout):
            try:
                response = self.session.get(f"{self.base_url}/api/health", timeout=1)
                if response.status_code == 200:
                    print(f"{GREEN}✓{NC} Backend is ready\n")
                    return True
            except:
                pass
            
            if i < timeout - 1:
                print(".", end="", flush=True)
            
        print(f"\n{RED}✗{NC} Backend is not responding")
        print(f"Make sure the backend is running on {self.base_url}\n")
        return False
    
    def run_all_tests(self):
        """Run all test suites"""
        print(f"{BLUE}╔════════════════════════════════════════════════════╗{NC}")
        print(f"{BLUE}║{NC}  Service Manager Dashboard - API Test Suite    {BLUE}║{NC}")
        print(f"{BLUE}╚════════════════════════════════════════════════════╝{NC}")
        print(f"\nTesting backend: {self.base_url}\n")
        
        # Wait for backend
        if not self.wait_for_backend():
            return False
        
        # Health & Status Tests
        self.print_header("Health & Status Tests")
        self.test_endpoint("Health Check", "GET", "/api/health", expected_status=200)
        
        # Status Endpoint Tests
        self.print_header("Status Endpoint Tests")
        self.test_endpoint("Get Status", "GET", "/api/status", expected_status=200)
        self.test_endpoint("Get Status (Invalid)", "GET", "/api/status/invalid", expected_status=404)
        
        # Control Endpoint Tests
        self.print_header("Control Endpoint Tests")
        self.test_endpoint(
            "Start Service",
            "POST",
            "/api/control",
            data={"action": "start"},
            expected_status=200
        )
        self.test_endpoint(
            "Stop Service",
            "POST",
            "/api/control",
            data={"action": "stop"},
            expected_status=200
        )
        self.test_endpoint(
            "Restart Service",
            "POST",
            "/api/control",
            data={"action": "restart"},
            expected_status=200
        )
        
        # Logs Endpoint Tests
        self.print_header("Logs Endpoint Tests")
        self.test_endpoint(
            "Get Platform Logs",
            "GET",
            "/api/logs?service=platform",
            expected_status=200
        )
        self.test_endpoint(
            "Get Logs with Search",
            "GET",
            "/api/logs?service=platform&search=INFO",
            expected_status=200
        )
        self.test_endpoint(
            "Get Limited Logs",
            "GET",
            "/api/logs?service=platform&lines=50",
            expected_status=200
        )
        
        # Download Tests
        self.print_header("Download Endpoint Tests")
        self.test_endpoint(
            "Download Platform Logs",
            "GET",
            "/api/logs/download?service=platform",
            expected_status=200
        )
        
        # Error Cases
        self.print_header("Error Handling Tests")
        self.test_endpoint(
            "Get Logs (Nonexistent Service)",
            "GET",
            "/api/logs?service=nonexistent",
            expected_status=200  # Should return empty, not error
        )
        
        # Print Summary
        self.print_summary()
        
        return self.tests_failed == 0
    
    def print_summary(self):
        """Print test summary"""
        total = self.tests_passed + self.tests_failed
        
        print(f"\n{BLUE}{'═' * 50}{NC}")
        print(f"{BLUE}  Test Summary{NC}")
        print(f"{BLUE}{'═' * 50}{NC}\n")
        print(f"  Total Tests:  {total}")
        print(f"  {GREEN}Passed:       {self.tests_passed}{NC}")
        print(f"  {RED}Failed:       {self.tests_failed}{NC}")
        print(f"\n{BLUE}{'═' * 50}{NC}\n")
        
        if self.tests_failed == 0:
            print(f"{GREEN}✓ All tests passed!{NC}\n")
            print("You can now access the dashboard:")
            print("  Frontend: http://localhost:5173")
            print("  Backend API: http://localhost:8080")
            print("  API Docs: http://localhost:8080/api/docs\n")
            return True
        else:
            print(f"{RED}✗ Some tests failed.{NC}\n")
            print("Check the backend logs for more information.\n")
            return False
    
    def test_with_data(self):
        """Test endpoints with sample data"""
        self.print_header("Sample Data Collection")
        
        try:
            # Get status
            response = self.session.get(f"{self.base_url}/api/status")
            if response.status_code == 200:
                data = response.json()
                print(f"Current Status: {data['status']}")
                print(f"Platform: {data['platform']['name']} - {'Running' if data['platform']['running'] else 'Stopped'}")
                print(f"Services: {len(data['services'])}")
                for service in data['services']:
                    status = '🟢 Running' if service['running'] else '🔴 Stopped'
                    print(f"  - {service['name']}: {status}")
                return True
        except Exception as e:
            print(f"Error: {e}")
            return False
        
        return False


def main():
    """Main entry point"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    
    tester = APITester(base_url)
    
    # Run all tests
    success = tester.run_all_tests()
    
    # Show sample data if successful
    if success:
        tester.test_with_data()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Test interrupted by user{NC}\n")
        sys.exit(130)
    except Exception as e:
        print(f"\n{RED}Error: {e}{NC}\n")
        sys.exit(1)

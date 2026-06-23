"""
Integration test for Admin Timetable OCR AI feature.
Tests complete end-to-end workflow with real timetable images and edge cases.

Run with: python test_integration_timetable.py
"""
import asyncio
import base64
import io
import json
import os
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from PIL import Image
import httpx

# Test configuration
BASE_URL = os.getenv("API_URL", "http://localhost:8000")
TEST_EMAIL = "academic.admin@test.edu"
TEST_PASSWORD = "test123"

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

class TimetableIntegrationTest:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.token = None
        self.test_results = []
        
    def log(self, message, level="INFO"):
        """Log a message with color coding"""
        if level == "SUCCESS":
            print(f"{GREEN}✓ {message}{RESET}")
        elif level == "ERROR":
            print(f"{RED}✗ {message}{RESET}")
        elif level == "WARNING":
            print(f"{YELLOW}⚠ {message}{RESET}")
        else:
            print(f"{BLUE}• {message}{RESET}")
    
    def add_result(self, test_name, passed, message=""):
        """Record test result"""
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "message": message
        })
        if passed:
            self.log(f"{test_name}: {message}", "SUCCESS")
        else:
            self.log(f"{test_name}: {message}", "ERROR")
    
    async def authenticate(self):
        """Authenticate and get access token"""
        self.log(f"Authenticating as {TEST_EMAIL}...")
        try:
            response = await self.client.post(
                f"{BASE_URL}/auth/demo-login",
                json={"email": TEST_EMAIL}
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.log(f"Authenticated successfully", "SUCCESS")
                return True
            else:
                self.log(f"Authentication failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Authentication error: {str(e)}", "ERROR")
            return False
    
    def get_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}"}
    
    async def test_file_type_validation(self):
        """Test 1: File type validation - unsupported format"""
        self.log("\n=== Test 1: File Type Validation ===")
        
        # Create a text file
        file_content = b"This is not an image"
        files = {"file": ("test.txt", file_content, "text/plain")}
        
        try:
            response = await self.client.post(
                f"{BASE_URL}/api/academic/timetable/upload",
                headers=self.get_headers(),
                files=files
            )
            
            data = response.json()
            if response.status_code == 200 and not data["success"]:
                expected_msg = "Unsupported file format"
                if expected_msg in data["message"]:
                    self.add_result("File type validation", True, "Correctly rejected non-image file")
                else:
                    self.add_result("File type validation", False, f"Wrong error message: {data['message']}")
            else:
                self.add_result("File type validation", False, f"Expected error, got status {response.status_code}")
        except Exception as e:
            self.add_result("File type validation", False, str(e))
    
    async def test_file_size_validation(self):
        """Test 2: File size validation - oversized file"""
        self.log("\n=== Test 2: File Size Validation ===")
        
        # Create a large image (>10MB)
        large_image = Image.new("RGB", (4000, 4000), color="white")
        img_bytes = io.BytesIO()
        large_image.save(img_bytes, format="JPEG", quality=100)
        img_bytes.seek(0)
        
        files = {"file": ("large.jpg", img_bytes, "image/jpeg")}
        
        try:
            response = await self.client.post(
                f"{BASE_URL}/api/academic/timetable/upload",
                headers=self.get_headers(),
                files=files
            )
            
            data = response.json()
            if response.status_code == 200 and not data["success"]:
                expected_msg = "exceeds the maximum limit"
                if expected_msg in data["message"]:
                    self.add_result("File size validation", True, "Correctly rejected oversized file")
                else:
                    self.add_result("File size validation", False, f"Wrong error message: {data['message']}")
            else:
                self.add_result("File size validation", False, f"Expected error, got status {response.status_code}")
        except Exception as e:
            self.add_result("File size validation", False, str(e))
    
    async def test_empty_file(self):
        """Test 3: Empty file validation"""
        self.log("\n=== Test 3: Empty File Validation ===")
        
        files = {"file": ("empty.jpg", b"", "image/jpeg")}
        
        try:
            response = await self.client.post(
                f"{BASE_URL}/api/academic/timetable/upload",
                headers=self.get_headers(),
                files=files
            )
            
            data = response.json()
            if response.status_code == 200 and not data["success"]:
                expected_msg = "empty"
                if expected_msg.lower() in data["message"].lower():
                    self.add_result("Empty file validation", True, "Correctly rejected empty file")
                else:
                    self.add_result("Empty file validation", False, f"Wrong error message: {data['message']}")
            else:
                self.add_result("Empty file validation", False, f"Expected error, got status {response.status_code}")
        except Exception as e:
            self.add_result("Empty file validation", False, str(e))
    
    async def test_non_timetable_image(self):
        """Test 4: Non-timetable image (e.g., landscape photo)"""
        self.log("\n=== Test 4: Non-Timetable Image ===")
        
        # Create a simple colored image (not a timetable)
        img = Image.new("RGB", (800, 600), color="skyblue")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)
        
        files = {"file": ("landscape.jpg", img_bytes, "image/jpeg")}
        
        try:
            response = await self.client.post(
                f"{BASE_URL}/api/academic/timetable/upload",
                headers=self.get_headers(),
                files=files
            )
            
            data = response.json()
            if response.status_code == 200:
                # Should either succeed with 0 entries or return error
                if data["success"] and len(data["entries"]) == 0:
                    self.add_result("Non-timetable image", True, "Returned 0 entries as expected")
                elif not data["success"]:
                    self.add_result("Non-timetable image", True, "Returned error as expected")
                else:
                    self.add_result("Non-timetable image", False, f"Unexpected result: {len(data['entries'])} entries")
            else:
                self.add_result("Non-timetable image", False, f"Unexpected status {response.status_code}")
        except Exception as e:
            self.add_result("Non-timetable image", False, str(e))
    
    async def test_corrupted_image(self):
        """Test 5: Corrupted image file"""
        self.log("\n=== Test 5: Corrupted Image ===")
        
        # Create invalid JPEG data
        corrupted_data = b"\xFF\xD8\xFF\xE0\x00\x10JFIF" + b"\x00" * 100  # Invalid JPEG
        files = {"file": ("corrupted.jpg", corrupted_data, "image/jpeg")}
        
        try:
            response = await self.client.post(
                f"{BASE_URL}/api/academic/timetable/upload",
                headers=self.get_headers(),
                files=files
            )
            
            data = response.json()
            # Should handle gracefully - either parse error or empty result
            if response.status_code == 200:
                self.add_result("Corrupted image", True, f"Handled gracefully: {data['message']}")
            else:
                self.add_result("Corrupted image", False, f"Unexpected status {response.status_code}")
        except Exception as e:
            self.add_result("Corrupted image", False, str(e))
    
    async def test_real_timetable_upload(self):
        """Test 6: Real timetable image upload (if available)"""
        self.log("\n=== Test 6: Real Timetable Upload ===")
        
        test_image_path = Path(__file__).parent / "test-timetable.jpg"
        
        if not test_image_path.exists():
            self.add_result("Real timetable upload", False, "Test image not found")
            return
        
        try:
            with open(test_image_path, "rb") as f:
                files = {"file": ("timetable.jpg", f, "image/jpeg")}
                
                response = await self.client.post(
                    f"{BASE_URL}/api/academic/timetable/upload",
                    headers=self.get_headers(),
                    files=files
                )
                
                data = response.json()
                if response.status_code == 200:
                    if data["success"]:
                        self.add_result(
                            "Real timetable upload",
                            True,
                            f"Parsed {len(data['entries'])} entries. Raw text length: {len(data.get('extracted_text', ''))}"
                        )
                        # Store entries for next test
                        self.parsed_entries = data["entries"]
                    else:
                        self.add_result("Real timetable upload", False, f"Parse failed: {data['message']}")
                else:
                    self.add_result("Real timetable upload", False, f"Status {response.status_code}")
        except Exception as e:
            self.add_result("Real timetable upload", False, str(e))
    
    async def test_atomic_replacement(self):
        """Test 7: Atomic replacement - old entries are deleted"""
        self.log("\n=== Test 7: Atomic Replacement ===")
        
        if not hasattr(self, 'parsed_entries') or not self.parsed_entries:
            self.add_result("Atomic replacement", False, "No parsed entries from previous test")
            return
        
        try:
            # First, confirm the parsed entries
            response1 = await self.client.post(
                f"{BASE_URL}/api/academic/timetable/confirm",
                headers=self.get_headers(),
                json={"entries": self.parsed_entries}
            )
            
            if response1.status_code != 200:
                self.add_result("Atomic replacement", False, f"First save failed: {response1.status_code}")
                return
            
            data1 = response1.json()
            first_count = data1.get("entries_created", 0)
            self.log(f"First save: {first_count} entries created")
            
            # Now upload a different set (just one entry)
            new_entries = [{
                "day_of_week": "Monday",
                "start_time": "08:00",
                "end_time": "09:00",
                "subject": "Test Subject",
                "room": "T101",
                "faculty_name": "Test Faculty",
                "semester": 1
            }]
            
            response2 = await self.client.post(
                f"{BASE_URL}/api/academic/timetable/confirm",
                headers=self.get_headers(),
                json={"entries": new_entries}
            )
            
            if response2.status_code != 200:
                self.add_result("Atomic replacement", False, f"Second save failed: {response2.status_code}")
                return
            
            data2 = response2.json()
            second_count = data2.get("entries_created", 0)
            
            # Now fetch all entries - should only have the new one
            response3 = await self.client.get(
                f"{BASE_URL}/api/academic/timetable",
                headers=self.get_headers()
            )
            
            if response3.status_code != 200:
                self.add_result("Atomic replacement", False, f"Fetch failed: {response3.status_code}")
                return
            
            all_entries = response3.json()
            
            if len(all_entries) == second_count:
                self.add_result(
                    "Atomic replacement",
                    True,
                    f"Old entries deleted. Only {len(all_entries)} new entries exist"
                )
            else:
                self.add_result(
                    "Atomic replacement",
                    False,
                    f"Expected {second_count} entries, found {len(all_entries)}"
                )
        except Exception as e:
            self.add_result("Atomic replacement", False, str(e))
    
    async def test_validation_error_messages(self):
        """Test 8: User-friendly error messages for validation"""
        self.log("\n=== Test 8: Validation Error Messages ===")
        
        # Test invalid day_of_week
        invalid_entries = [{
            "day_of_week": "Funday",  # Invalid day
            "start_time": "09:00",
            "end_time": "10:00",
            "subject": "Test",
            "semester": 1
        }]
        
        try:
            response = await self.client.post(
                f"{BASE_URL}/api/academic/timetable/confirm",
                headers=self.get_headers(),
                json={"entries": invalid_entries}
            )
            
            # Should get validation error from Pydantic
            if response.status_code == 422:
                self.add_result("Validation error messages", True, "Validation error caught (422)")
            elif response.status_code == 200:
                data = response.json()
                if data["entries_created"] == 0:
                    self.add_result("Validation error messages", True, "Invalid entry skipped")
                else:
                    self.add_result("Validation error messages", False, "Invalid entry was saved")
            else:
                self.add_result("Validation error messages", False, f"Unexpected status {response.status_code}")
        except Exception as e:
            self.add_result("Validation error messages", False, str(e))
    
    async def test_authentication_required(self):
        """Test 9: Authentication is required"""
        self.log("\n=== Test 9: Authentication Required ===")
        
        img = Image.new("RGB", (100, 100), color="white")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)
        
        files = {"file": ("test.jpg", img_bytes, "image/jpeg")}
        
        try:
            # Call without auth token
            response = await self.client.post(
                f"{BASE_URL}/api/academic/timetable/upload",
                files=files
            )
            
            if response.status_code == 401:
                self.add_result("Authentication required", True, "Correctly returned 401")
            else:
                self.add_result("Authentication required", False, f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.add_result("Authentication required", False, str(e))
    
    async def test_empty_entries_confirmation(self):
        """Test 10: Cannot confirm empty entries list"""
        self.log("\n=== Test 10: Empty Entries Validation ===")
        
        try:
            response = await self.client.post(
                f"{BASE_URL}/api/academic/timetable/confirm",
                headers=self.get_headers(),
                json={"entries": []}
            )
            
            # Should get validation error
            if response.status_code == 422:
                self.add_result("Empty entries validation", True, "Correctly rejected empty list")
            elif response.status_code == 400:
                self.add_result("Empty entries validation", True, "Correctly rejected empty list")
            else:
                self.add_result("Empty entries validation", False, f"Expected error, got {response.status_code}")
        except Exception as e:
            self.add_result("Empty entries validation", False, str(e))
    
    async def cleanup(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}TEST SUMMARY{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")
        
        passed = sum(1 for r in self.test_results if r["passed"])
        failed = len(self.test_results) - passed
        
        print(f"\nTotal Tests: {len(self.test_results)}")
        print(f"{GREEN}Passed: {passed}{RESET}")
        print(f"{RED}Failed: {failed}{RESET}")
        
        if failed > 0:
            print(f"\n{RED}Failed Tests:{RESET}")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  {RED}✗{RESET} {result['test']}: {result['message']}")
        
        print(f"\n{BLUE}{'='*60}{RESET}")
        
        if failed == 0:
            print(f"{GREEN}🎉 All tests passed!{RESET}\n")
        else:
            print(f"{RED}⚠ Some tests failed. Please review.{RESET}\n")
    
    async def run_all_tests(self):
        """Run all integration tests"""
        print(f"{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}TIMETABLE OCR AI - INTEGRATION TEST SUITE{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")
        print(f"Base URL: {BASE_URL}")
        print(f"Test User: {TEST_EMAIL}")
        print(f"{BLUE}{'='*60}{RESET}\n")
        
        # Authenticate first
        if not await self.authenticate():
            print(f"{RED}Authentication failed. Cannot proceed with tests.{RESET}")
            return
        
        # Run all tests
        await self.test_file_type_validation()
        await self.test_file_size_validation()
        await self.test_empty_file()
        await self.test_non_timetable_image()
        await self.test_corrupted_image()
        await self.test_real_timetable_upload()
        await self.test_atomic_replacement()
        await self.test_validation_error_messages()
        await self.test_authentication_required()
        await self.test_empty_entries_confirmation()
        
        # Print summary
        self.print_summary()
        
        # Cleanup
        await self.cleanup()

async def main():
    """Main entry point"""
    test_suite = TimetableIntegrationTest()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())

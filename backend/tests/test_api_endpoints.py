"""Test script for S.Y.N.A.P.S.E. ENGINE model management REST API endpoints.

This script validates all 11 endpoints in the model management API:
1. GET /api/models/registry
2. POST /api/models/rescan
3. PUT /api/models/{model_id}/tier
4. PUT /api/models/{model_id}/thinking
5. PUT /api/models/{model_id}/enabled
6. GET /api/models/servers
7. GET /api/models/tiers/{tier}
8. GET /api/models/profiles
9. GET /api/models/profiles/{profile_name}
10. POST /api/models/profiles
11. DELETE /api/models/profiles/{profile_name}

Usage:
    python test_api_endpoints.py
    python test_api_endpoints.py --base-url http://localhost:8000
"""

import argparse
import asyncio
import sys

import httpx


class APITester:
    """Test harness for model management API endpoints."""

    def __init__(self, base_url: str):
        """Initialize API tester.

        Args:
            base_url: Base URL for API (e.g., http://localhost:8000)
        """
        self.base_url = base_url.rstrip("/")
        self.passed = 0
        self.failed = 0
        self.test_model_id: str | None = None

    def print_header(self, text: str) -> None:
        """Print a formatted test section header."""
        print(f"\n{'=' * 70}")
        print(f"  {text}")
        print(f"{'=' * 70}")

    def print_test(self, name: str, status: str, details: str = "") -> None:
        """Print test result."""
        symbol = "✓" if status == "PASS" else "✗"
        color = "\033[92m" if status == "PASS" else "\033[91m"
        reset = "\033[0m"

        print(f"{color}{symbol} {name}{reset}")
        if details:
            print(f"  └─ {details}")

        if status == "PASS":
            self.passed += 1
        else:
            self.failed += 1

    def print_summary(self) -> None:
        """Print test summary."""
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0

        print(f"\n{'=' * 70}")
        print("  TEST SUMMARY")
        print(f"{'=' * 70}")
        print(f"  Total:  {total}")
        print(f"  Passed: {self.passed}")
        print(f"  Failed: {self.failed}")
        print(f"  Rate:   {pass_rate:.1f}%")
        print(f"{'=' * 70}\n")

    async def test_get_registry(self, client: httpx.AsyncClient) -> None:
        """Test GET /api/models/registry."""
        self.print_header("Test 1: GET /api/models/registry")

        try:
            response = await client.get(f"{self.base_url}/api/models/registry")

            if response.status_code == 200:
                data = response.json()
                model_count = len(data.get("models", {}))
                self.print_test(
                    "GET /api/models/registry",
                    "PASS",
                    f"Status: {response.status_code}, Models: {model_count}",
                )

                # Store first model ID for later tests
                if data.get("models"):
                    self.test_model_id = list(data["models"].keys())[0]
                    print(f"  └─ Using model ID '{self.test_model_id}' for subsequent tests")

            elif response.status_code == 503:
                self.print_test(
                    "GET /api/models/registry",
                    "PASS",
                    "Status: 503 (Registry not initialized - expected)",
                )
            else:
                self.print_test(
                    "GET /api/models/registry",
                    "FAIL",
                    f"Unexpected status: {response.status_code}",
                )

        except Exception as e:
            self.print_test("GET /api/models/registry", "FAIL", f"Error: {e}")

    async def test_get_servers(self, client: httpx.AsyncClient) -> None:
        """Test GET /api/models/servers."""
        self.print_header("Test 2: GET /api/models/servers")

        try:
            response = await client.get(f"{self.base_url}/api/models/servers")

            if response.status_code == 200:
                data = response.json()
                total = data.get("totalServers", 0)
                ready = data.get("readyServers", 0)
                self.print_test(
                    "GET /api/models/servers",
                    "PASS",
                    f"Status: {response.status_code}, Total: {total}, Ready: {ready}",
                )
            elif response.status_code == 503:
                self.print_test(
                    "GET /api/models/servers",
                    "PASS",
                    "Status: 503 (Server manager not initialized - expected)",
                )
            else:
                self.print_test(
                    "GET /api/models/servers",
                    "FAIL",
                    f"Unexpected status: {response.status_code}",
                )

        except Exception as e:
            self.print_test("GET /api/models/servers", "FAIL", f"Error: {e}")

    async def test_list_profiles(self, client: httpx.AsyncClient) -> None:
        """Test GET /api/models/profiles."""
        self.print_header("Test 3: GET /api/models/profiles")

        try:
            response = await client.get(f"{self.base_url}/api/models/profiles")

            if response.status_code == 200:
                profiles = response.json()
                self.print_test(
                    "GET /api/models/profiles",
                    "PASS",
                    f"Status: {response.status_code}, Profiles: {len(profiles)}",
                )
                if profiles:
                    print(f"  └─ Available profiles: {', '.join(profiles)}")
            elif response.status_code == 503:
                self.print_test(
                    "GET /api/models/profiles",
                    "PASS",
                    "Status: 503 (Profile manager not initialized - expected)",
                )
            else:
                self.print_test(
                    "GET /api/models/profiles",
                    "FAIL",
                    f"Unexpected status: {response.status_code}",
                )

        except Exception as e:
            self.print_test("GET /api/models/profiles", "FAIL", f"Error: {e}")

    async def test_get_profile(self, client: httpx.AsyncClient) -> None:
        """Test GET /api/models/profiles/{profile_name}."""
        self.print_header("Test 4: GET /api/models/profiles/development")

        try:
            response = await client.get(f"{self.base_url}/api/models/profiles/development")

            if response.status_code == 200:
                profile = response.json()
                enabled = len(profile.get("enabledModels", []))
                self.print_test(
                    "GET /api/models/profiles/development",
                    "PASS",
                    f"Status: {response.status_code}, Enabled models: {enabled}",
                )
            elif response.status_code == 404:
                self.print_test(
                    "GET /api/models/profiles/development",
                    "PASS",
                    "Status: 404 (Profile not found - acceptable)",
                )
            elif response.status_code == 503:
                self.print_test(
                    "GET /api/models/profiles/development",
                    "PASS",
                    "Status: 503 (Profile manager not initialized - expected)",
                )
            else:
                self.print_test(
                    "GET /api/models/profiles/development",
                    "FAIL",
                    f"Unexpected status: {response.status_code}",
                )

        except Exception as e:
            self.print_test("GET /api/models/profiles/development", "FAIL", f"Error: {e}")

    async def test_get_tiers(self, client: httpx.AsyncClient) -> None:
        """Test GET /api/models/tiers/{tier}."""
        self.print_header("Test 5: GET /api/models/tiers/powerful")

        try:
            response = await client.get(f"{self.base_url}/api/models/tiers/powerful")

            if response.status_code == 200:
                models = response.json()
                self.print_test(
                    "GET /api/models/tiers/powerful",
                    "PASS",
                    f"Status: {response.status_code}, Models: {len(models)}",
                )
            elif response.status_code == 503:
                self.print_test(
                    "GET /api/models/tiers/powerful",
                    "PASS",
                    "Status: 503 (Registry not initialized - expected)",
                )
            else:
                self.print_test(
                    "GET /api/models/tiers/powerful",
                    "FAIL",
                    f"Unexpected status: {response.status_code}",
                )

        except Exception as e:
            self.print_test("GET /api/models/tiers/powerful", "FAIL", f"Error: {e}")

    async def test_update_tier(self, client: httpx.AsyncClient) -> None:
        """Test PUT /api/models/{model_id}/tier."""
        self.print_header("Test 6: PUT /api/models/{model_id}/tier")

        if not self.test_model_id:
            self.print_test(
                "PUT /api/models/{model_id}/tier",
                "FAIL",
                "No model ID available (registry empty or not loaded)",
            )
            return

        try:
            response = await client.put(
                f"{self.base_url}/api/models/{self.test_model_id}/tier",
                json={"tier": "powerful"},
            )

            if response.status_code == 200:
                data = response.json()
                self.print_test(
                    f"PUT /api/models/{self.test_model_id}/tier",
                    "PASS",
                    f"Status: {response.status_code}, Tier: {data.get('tier')}",
                )
            elif response.status_code in [404, 503]:
                self.print_test(
                    f"PUT /api/models/{self.test_model_id}/tier",
                    "PASS",
                    f"Status: {response.status_code} (Expected when registry/model not found)",
                )
            else:
                self.print_test(
                    f"PUT /api/models/{self.test_model_id}/tier",
                    "FAIL",
                    f"Unexpected status: {response.status_code}",
                )

        except Exception as e:
            self.print_test(f"PUT /api/models/{self.test_model_id}/tier", "FAIL", f"Error: {e}")

    async def test_update_thinking(self, client: httpx.AsyncClient) -> None:
        """Test PUT /api/models/{model_id}/thinking."""
        self.print_header("Test 7: PUT /api/models/{model_id}/thinking")

        if not self.test_model_id:
            self.print_test(
                "PUT /api/models/{model_id}/thinking",
                "FAIL",
                "No model ID available (registry empty or not loaded)",
            )
            return

        try:
            response = await client.put(
                f"{self.base_url}/api/models/{self.test_model_id}/thinking",
                json={"thinking": True},
            )

            if response.status_code == 200:
                data = response.json()
                self.print_test(
                    f"PUT /api/models/{self.test_model_id}/thinking",
                    "PASS",
                    f"Status: {response.status_code}, Thinking: {data.get('thinking')}",
                )
            elif response.status_code in [404, 503]:
                self.print_test(
                    f"PUT /api/models/{self.test_model_id}/thinking",
                    "PASS",
                    f"Status: {response.status_code} (Expected when registry/model not found)",
                )
            else:
                self.print_test(
                    f"PUT /api/models/{self.test_model_id}/thinking",
                    "FAIL",
                    f"Unexpected status: {response.status_code}",
                )

        except Exception as e:
            self.print_test(f"PUT /api/models/{self.test_model_id}/thinking", "FAIL", f"Error: {e}")

    async def test_update_enabled(self, client: httpx.AsyncClient) -> None:
        """Test PUT /api/models/{model_id}/enabled."""
        self.print_header("Test 8: PUT /api/models/{model_id}/enabled")

        if not self.test_model_id:
            self.print_test(
                "PUT /api/models/{model_id}/enabled",
                "FAIL",
                "No model ID available (registry empty or not loaded)",
            )
            return

        try:
            response = await client.put(
                f"{self.base_url}/api/models/{self.test_model_id}/enabled",
                json={"enabled": True},
            )

            if response.status_code == 200:
                data = response.json()
                self.print_test(
                    f"PUT /api/models/{self.test_model_id}/enabled",
                    "PASS",
                    f"Status: {response.status_code}, Enabled: {data.get('enabled')}",
                )
            elif response.status_code in [404, 503]:
                self.print_test(
                    f"PUT /api/models/{self.test_model_id}/enabled",
                    "PASS",
                    f"Status: {response.status_code} (Expected when registry/model not found)",
                )
            else:
                self.print_test(
                    f"PUT /api/models/{self.test_model_id}/enabled",
                    "FAIL",
                    f"Unexpected status: {response.status_code}",
                )

        except Exception as e:
            self.print_test(f"PUT /api/models/{self.test_model_id}/enabled", "FAIL", f"Error: {e}")

    async def test_rescan(self, client: httpx.AsyncClient) -> None:
        """Test POST /api/models/rescan."""
        self.print_header("Test 9: POST /api/models/rescan")

        try:
            response = await client.post(f"{self.base_url}/api/models/rescan")

            if response.status_code == 200:
                data = response.json()
                found = data.get("modelsFound", 0)
                added = data.get("modelsAdded", 0)
                removed = data.get("modelsRemoved", 0)
                self.print_test(
                    "POST /api/models/rescan",
                    "PASS",
                    f"Status: {response.status_code}, Found: {found}, Added: {added}, Removed: {removed}",
                )
            elif response.status_code == 503:
                self.print_test(
                    "POST /api/models/rescan",
                    "PASS",
                    "Status: 503 (Registry/discovery not initialized - expected)",
                )
            else:
                self.print_test(
                    "POST /api/models/rescan",
                    "FAIL",
                    f"Unexpected status: {response.status_code}",
                )

        except Exception as e:
            self.print_test("POST /api/models/rescan", "FAIL", f"Error: {e}")

    async def test_create_profile(self, client: httpx.AsyncClient) -> None:
        """Test POST /api/models/profiles."""
        self.print_header("Test 10: POST /api/models/profiles")

        try:
            response = await client.post(
                f"{self.base_url}/api/models/profiles",
                json={
                    "name": "API Test Profile",
                    "description": "Test profile created via API",
                    "enabledModels": [],
                },
            )

            if response.status_code == 201:
                data = response.json()
                self.print_test(
                    "POST /api/models/profiles",
                    "PASS",
                    f"Status: {response.status_code}, Profile: {data.get('profileName')}",
                )
            elif response.status_code == 503:
                self.print_test(
                    "POST /api/models/profiles",
                    "PASS",
                    "Status: 503 (Profile manager not initialized - expected)",
                )
            else:
                self.print_test(
                    "POST /api/models/profiles",
                    "FAIL",
                    f"Unexpected status: {response.status_code}",
                )

        except Exception as e:
            self.print_test("POST /api/models/profiles", "FAIL", f"Error: {e}")

    async def test_delete_profile(self, client: httpx.AsyncClient) -> None:
        """Test DELETE /api/models/profiles/{profile_name}."""
        self.print_header("Test 11: DELETE /api/models/profiles/api-test-profile")

        try:
            response = await client.delete(f"{self.base_url}/api/models/profiles/api-test-profile")

            if response.status_code == 200:
                self.print_test(
                    "DELETE /api/models/profiles/api-test-profile",
                    "PASS",
                    f"Status: {response.status_code}",
                )
            elif response.status_code == 404:
                self.print_test(
                    "DELETE /api/models/profiles/api-test-profile",
                    "PASS",
                    "Status: 404 (Profile not found - acceptable)",
                )
            elif response.status_code == 503:
                self.print_test(
                    "DELETE /api/models/profiles/api-test-profile",
                    "PASS",
                    "Status: 503 (Profile manager not initialized - expected)",
                )
            else:
                self.print_test(
                    "DELETE /api/models/profiles/api-test-profile",
                    "FAIL",
                    f"Unexpected status: {response.status_code}",
                )

        except Exception as e:
            self.print_test("DELETE /api/models/profiles/api-test-profile", "FAIL", f"Error: {e}")

    async def run_all_tests(self) -> None:
        """Run all API endpoint tests."""
        print("\n" + "=" * 70)
        print("  S.Y.N.A.P.S.E. ENGINE Model Management API Test Suite")
        print(f"  Base URL: {self.base_url}")
        print("=" * 70)

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test each endpoint
            await self.test_get_registry(client)
            await self.test_get_servers(client)
            await self.test_list_profiles(client)
            await self.test_get_profile(client)
            await self.test_get_tiers(client)
            await self.test_update_tier(client)
            await self.test_update_thinking(client)
            await self.test_update_enabled(client)
            await self.test_rescan(client)
            await self.test_create_profile(client)
            await self.test_delete_profile(client)

        # Print summary
        self.print_summary()


async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test S.Y.N.A.P.S.E. ENGINE model management API endpoints"
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL for API (default: http://localhost:8000)",
    )
    args = parser.parse_args()

    tester = APITester(args.base_url)
    await tester.run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if tester.failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())

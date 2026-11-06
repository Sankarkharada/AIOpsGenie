import unittest

from app import create_app


class TestSystemAPI(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_system_api_status(self):
        response = self.client.get("/api/system")
        self.assertEqual(response.status_code, 200)

    def test_system_api_metrics(self):
        response = self.client.get("/api/system")
        data = response.get_json()

        self.assertIn("cpu_percent", data)
        self.assertIn("memory_percent", data)
        self.assertIn("disk_percent", data)
        self.assertIn("health", data)

    def test_health_value(self):
        response = self.client.get("/api/system")
        data = response.get_json()

        self.assertIn(
            data["health"],
            ["HEALTHY", "WARNING", "CRITICAL"]
        )


if __name__ == "__main__":
    unittest.main()
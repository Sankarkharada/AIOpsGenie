import unittest

from app.tools.system_tool import get_system_metrics


class TestSystemMonitoring(unittest.TestCase):

    def test_system_metrics(self):
        metrics = get_system_metrics()

        required_fields = [
            "cpu_percent",
            "memory_percent",
            "memory_used_gb",
            "memory_total_gb",
            "disk_percent",
            "disk_used_gb",
            "disk_total_gb",
            "health",
            "message"
        ]

        for field in required_fields:
            self.assertIn(field, metrics)

    def test_metric_ranges(self):
        metrics = get_system_metrics()

        self.assertGreaterEqual(metrics["cpu_percent"], 0)
        self.assertLessEqual(metrics["cpu_percent"], 100)

        self.assertGreaterEqual(metrics["memory_percent"], 0)
        self.assertLessEqual(metrics["memory_percent"], 100)

        self.assertGreaterEqual(metrics["disk_percent"], 0)
        self.assertLessEqual(metrics["disk_percent"], 100)

    def test_health_status(self):
        metrics = get_system_metrics()

        self.assertIn(
            metrics["health"],
            ["HEALTHY", "WARNING", "CRITICAL"]
        )


if __name__ == "__main__":
    unittest.main()
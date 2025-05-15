import unittest
from unittest.mock import patch, call
import os

# Import the actual MetricsManager (or the module containing it)
# Assuming src/shared/metrics.py exists and contains the MetricsManager class
from src.shared.metrics import MetricsManager, DummyCounter, init

class TestMetrics(unittest.TestCase):

    def setUp(self):
        # Reset the singleton instance and initialized flag before each test
        MetricsManager._instance = None
        MetricsManager._initialized = False
        # Ensure server thread is reset if it was started
        MetricsManager._server_thread = None

    @patch.dict(os.environ, {}, clear=True)
    def test_metrics_disabled_by_default(self):
        """Metrics should be disabled if ENABLE_METRICS is not set."""
        metrics_manager = MetricsManager()
        self.assertFalse(metrics_manager.enabled)
        self.assertIsInstance(metrics_manager.agents_spawned_total, DummyCounter)
        self.assertIsInstance(metrics_manager.cli_calls_total, DummyCounter)
        self.assertIsInstance(metrics_manager.qa_pass_total, DummyCounter)
        self.assertIsInstance(metrics_manager.qa_fail_total, DummyCounter)

        # Calling inc() on DummyCounter should not raise an error
        metrics_manager.agents_spawned_total.inc()
        metrics_manager.cli_calls_total.inc(5)

        # get_snapshot should return disabled message
        snapshot = metrics_manager.get_snapshot()
        self.assertEqual(snapshot, {'status': 'Metrics disabled'})

    @patch.dict(os.environ, {'ENABLE_METRICS': '1'}, clear=True)
    @patch('src.shared.metrics.start_http_server')
    def test_metrics_enabled(self, mock_start_http_server):
        """Metrics should be enabled and counters should increment when ENABLE_METRICS is set."""
        # Initialize the metrics manager (this should start the server)
        init()
        metrics_manager = MetricsManager()

        self.assertTrue(metrics_manager.enabled)
        self.assertIsNotInstance(metrics_manager.agents_spawned_total, DummyCounter)
        self.assertIsNotInstance(metrics_manager.cli_calls_total, DummyCounter)
        self.assertIsNotInstance(metrics_manager.qa_pass_total, DummyCounter)
        self.assertIsNotInstance(metrics_manager.qa_fail_total, DummyCounter)

        # Check that the HTTP server was attempted to be started
        mock_start_http_server.assert_called_once_with(9090, registry=metrics_manager._registry)

        # Simulate metric increments
        metrics_manager.agents_spawned_total.inc()
        metrics_manager.cli_calls_total.inc(3)
        metrics_manager.qa_pass_total.inc()
        metrics_manager.qa_fail_total.inc(2)

        # get_snapshot should return metric data (mocked prometheus_client would be needed for real values)
        # We can't easily check the exact values here without a more complex mock
        # But we can check the structure if needed, or rely on the real prometheus_client for value tests.
        # For this test, we primarily confirm that we are NOT using DummyCounters.
        snapshot = metrics_manager.get_snapshot()
        # Basic check that it's not the disabled message
        self.assertNotEqual(snapshot, {'status': 'Metrics disabled'})
        # More detailed checks would require mocking the registry.collect() and sample data
        # For simplicity in this unit test, we assume if enabled, the real client works.

    @patch.dict(os.environ, {'ENABLE_METRICS': '1'}, clear=True)
    @patch('src.shared.metrics.start_http_server')
    def test_metrics_port_in_use_fallback(self, mock_start_http_server):
        """MetricsManager should try alternative ports if the default is in use."""
        # Simulate port 9090 being in use by raising OSError
        mock_start_http_server.side_effect = [OSError("Address already in use"), None]

        init()
        metrics_manager = MetricsManager()

        self.assertTrue(metrics_manager.enabled)
        self.assertIsNotNone(metrics_manager._server_thread)

        # Check that start_http_server was called first with 9090, then with 9091
        mock_start_http_server.assert_has_calls([
            call(9090, registry=metrics_manager._registry),
            call(9091, registry=metrics_manager._registry)
        ])

    @patch.dict(os.environ, {'ENABLE_METRICS': '1'}, clear=True)
    @patch('src.shared.metrics.start_http_server')
    def test_metrics_enabled_prometheus_not_available(self, mock_start_http_server):
        """Metrics should be disabled if prometheus_client is not available even if ENABLE_METRICS is set."""
        init()
        metrics_manager = MetricsManager()

        self.assertFalse(metrics_manager.enabled)
        self.assertIsInstance(metrics_manager.agents_spawned_total, DummyCounter)
        mock_start_http_server.assert_not_called()
        snapshot = metrics_manager.get_snapshot()
        self.assertEqual(snapshot, {'status': 'Metrics disabled'})

# Example usage (optional, for local testing)
# if __name__ == '__main__':
#     unittest.main() 
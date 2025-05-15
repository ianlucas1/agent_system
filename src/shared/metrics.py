import os
from threading import Thread

try:
    from prometheus_client import Counter, start_http_server, CollectorRegistry
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

class DummyCounter:
    def inc(self, amount=1):
        pass

class MetricsManager:
    _instance = None
    _initialized = False
    _server_thread = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MetricsManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.enabled = os.environ.get('ENABLE_METRICS') is not None and os.environ.get('ENABLE_METRICS').lower() in ['true', '1', 'yes']
            if self.enabled and PROMETHEUS_AVAILABLE:
                self._registry = CollectorRegistry()
                self.agents_spawned_total = Counter('agents_spawned_total', 'Total number of agents spawned', registry=self._registry)
                self.cli_calls_total = Counter('cli_calls_total', 'Total number of CLI commands executed', registry=self._registry)
                self.qa_pass_total = Counter('qa_pass_total', 'Total number of QA gate passes', registry=self._registry)
                self.qa_fail_total = Counter('qa_fail_total', 'Total number of QA gate failures', registry=self._registry)
            else:
                self._registry = None # Set registry to None if metrics disabled or prometheus not available
                self.agents_spawned_total = DummyCounter()
                self.cli_calls_total = DummyCounter()
                self.qa_pass_total = DummyCounter()
                self.qa_fail_total = DummyCounter()

            if self.enabled and PROMETHEUS_AVAILABLE and not self._server_thread:
                # Start HTTP server in a separate thread
                def run_server(port):
                    try:
                        start_http_server(port, registry=self._registry)
                        print(f"Prometheus metrics server started on port {port}")
                    except OSError as e:
                        print(f"Port {port} already in use: {e}")
                        if port < 9095: # Try a few more ports
                             run_server(port + 1)
                        else:
                            print("Failed to start Prometheus server on multiple ports.")

                self._server_thread = Thread(target=run_server, args=(9090,), daemon=True)
                self._server_thread.start()

            self._initialized = True

    def get_snapshot(self):
        if self.enabled and PROMETHEUS_AVAILABLE:
            # This requires the text format exporter
            # For a simple snapshot, we can manually collect and format
            # A real implementation might use generate_latest or a custom collector
            metrics_data = {}
            for metric in self._registry.collect():
                metrics_data[metric.name] = {}
                for sample in metric.samples:
                     metrics_data[metric.name][sample.labels] = sample.value
            return metrics_data
        else:
            return {'status': 'Metrics disabled'}

def init():
    # Accessing the instance initializes it
    MetricsManager() 
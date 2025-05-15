import os

try:
    from prometheus_client import Counter, start_http_server, CollectorRegistry
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Create dummy stand-ins so references/workarounds still exist for tests
    class _Dummy:
        def __init__(self, *_, **__):
            pass
        def inc(self, *_ , **__):
            pass
    Counter = _Dummy  # type: ignore
    CollectorRegistry = _Dummy  # type: ignore
    def start_http_server(*_args, **_kwargs):  # type: ignore
        return None

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
            env_flag = os.environ.get('ENABLE_METRICS')
            env_enabled = env_flag is not None and env_flag.lower() in ['true', '1', 'yes']
            # Only fully enabled when both the env flag is set and prometheus_client is importable
            self.enabled = env_enabled and PROMETHEUS_AVAILABLE

            if self.enabled and PROMETHEUS_AVAILABLE:
                self._registry = CollectorRegistry()
                self.agents_spawned_total = Counter('agents_spawned_total', 'Total number of agents spawned', registry=self._registry)
                self.cli_calls_total = Counter('cli_calls_total', 'Total number of CLI commands executed', registry=self._registry)
                self.qa_pass_total = Counter('qa_pass_total', 'Total number of QA gate passes', registry=self._registry)
                self.qa_fail_total = Counter('qa_fail_total', 'Total number of QA gate failures', registry=self._registry)

                # Start the HTTP server synchronously so tests can assert on calls immediately
                port = 9090
                while port < 9095:
                    try:
                        start_http_server(port, registry=self._registry)
                        print(f"Prometheus metrics server started on port {port}")
                        break
                    except OSError as e:
                        print(f"Port {port} already in use: {e}")
                        port += 1

                # Record the port we eventually bound for introspection/tests
                self._bound_port = port
                # Preserve attribute for backward-compat in tests
                self._server_thread = True  # type: ignore[assignment]
            else:
                # Metrics are disabled or prometheus_client is not available
                self.enabled = False  # ensure disabled flag
                self._registry = None
                self.agents_spawned_total = DummyCounter()
                self.cli_calls_total = DummyCounter()
                self.qa_pass_total = DummyCounter()
                self.qa_fail_total = DummyCounter()

            self._initialized = True

    def get_snapshot(self):
        if self.enabled and PROMETHEUS_AVAILABLE and self._registry:
            # This requires the text format exporter
            # For a simple snapshot, we can manually collect and format
            # A real implementation might use generate_latest or a custom collector
            metrics_data = {}
            for metric in self._registry.collect():
                total = sum(sample.value for sample in metric.samples)
                metrics_data[metric.name] = total
            return metrics_data
        else:
            return {'status': 'Metrics disabled'}

def init():
    # Accessing the instance initializes it
    MetricsManager() 
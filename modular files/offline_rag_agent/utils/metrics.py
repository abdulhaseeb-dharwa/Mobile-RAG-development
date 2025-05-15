import time
from functools import wraps
from typing import Dict, Any, Callable
from collections import defaultdict
import threading

class MetricsCollector:
    def __init__(self):
        self._metrics = defaultdict(list)
        self._lock = threading.Lock()

    def record_metric(self, name: str, value: float):
        """Record a metric value."""
        with self._lock:
            self._metrics[name].append(value)

    def get_metric(self, name: str) -> list:
        """Get all recorded values for a metric."""
        with self._lock:
            return self._metrics.get(name, [])

    def get_metric_stats(self, name: str) -> Dict[str, float]:
        """Get statistics for a metric."""
        values = self.get_metric(name)
        if not values:
            return {}
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values)
        }

    def clear_metrics(self):
        """Clear all recorded metrics."""
        with self._lock:
            self._metrics.clear()

def track_time(metric_name: str):
    """Decorator to track execution time of functions."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                execution_time = time.time() - start_time
                metrics_collector.record_metric(metric_name, execution_time)
        return wrapper
    return decorator

# Global metrics collector instance
metrics_collector = MetricsCollector() 
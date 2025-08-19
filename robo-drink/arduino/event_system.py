import threading
from typing import Dict, List, Callable, Any
import time

class EventEmitter:
    def __init__(self):
        self._listeners: Dict[str, List[Callable[[Any], None]]] = {}
        self._lock = threading.Lock()

    def on(self, event_name: str, callback: Callable[[Any], None]):
        """Subscribe to an event"""
        with self._lock:
            if event_name not in self._listeners:
                self._listeners[event_name] = []
            self._listeners[event_name].append(callback)
    
    def off(self, event_name: str, callback: Callable[[Any], None]):
        """Unsubscribe from an event"""
        with self._lock:
            if event_name in self._listeners:
                try:
                    self._listeners[event_name].remove(callback)
                except ValueError:
                    pass
    
    def emit(self, event_name: str, data: Any):
        """Emit an event to all listeners"""
        listeners = []
        with self._lock:
            if event_name in self._listeners:
                listeners = self._listeners.get(event_name, []).copy()
            
        for callback in listeners:
            try:
                callback(data)
            except Exception as e:
                print(f"Error in event listener {callback}: {e}")
    
    def destroy(self):
        """Remove all listeners"""
        with self._lock:
            self._listeners.clear()

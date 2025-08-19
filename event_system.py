import threading
from typing import Dict, List, Callable, Any, Optional
import inspect
import asyncio

class EventEmitter:
    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        self._listeners: Dict[str, List[Callable[[Any], Any]]] = {}
        self._lock = threading.Lock()
        self._loop = loop

    def on(self, event_name: str, callback: Callable[[Any], Any]):
        with self._lock:
            self._listeners.setdefault(event_name, []).append(callback)

    def off(self, event_name: str, callback: Callable[[Any], Any]):
        with self._lock:
            if event_name in self._listeners:
                try:
                    self._listeners[event_name].remove(callback)
                except ValueError:
                    pass

    def emit(self, event_name: str, data: Any):
        with self._lock:
            listeners = list(self._listeners.get(event_name, []))

        for callback in listeners:
            try:
                if inspect.iscoroutinefunction(callback):
                    coro = callback(data)
                    self._schedule_coro(coro)
                else:
                    result = callback(data)
                    # If a sync callback returns a coroutine, schedule it too
                    if inspect.iscoroutine(result):
                        self._schedule_coro(result)
            except Exception as e:
                print(f"Error in event listener {callback}: {e}")

    def _schedule_coro(self, coro):
        loop = self._loop
        if loop is None:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(coro)
                return
            except RuntimeError:
                # No running loop in this thread; fall back to one-off run (blocking)
                asyncio.run(coro)
                return
        # We have a target loop (possibly in another thread)
        asyncio.run_coroutine_threadsafe(coro, loop)

    def destroy(self):
        with self._lock:
            self._listeners.clear()

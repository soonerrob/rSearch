import asyncio
from typing import Callable, List, Optional


class CancellationToken:
    """A token for managing cancellation of async operations."""
    
    def __init__(self):
        self._is_cancelled = False
        self._cancel_callbacks: List[Callable[[], None]] = []
        self._cleanup_callbacks: List[Callable[[], None]] = []
    
    @property
    def is_cancelled(self) -> bool:
        """Check if the operation has been cancelled."""
        return self._is_cancelled
    
    def cancel(self) -> None:
        """Cancel the operation."""
        if not self._is_cancelled:
            self._is_cancelled = True
            # Execute cancel callbacks
            for callback in self._cancel_callbacks:
                try:
                    callback()
                except Exception:
                    pass  # Ignore callback errors
    
    def throw_if_cancelled(self) -> None:
        """Raise CancellationError if the operation is cancelled."""
        if self._is_cancelled:
            raise asyncio.CancelledError()
    
    async def throw_if_cancelled_async(self) -> None:
        """Asynchronously raise CancellationError if the operation is cancelled."""
        if self._is_cancelled:
            raise asyncio.CancelledError()
    
    def register_cancel_callback(self, callback: Callable[[], None]) -> None:
        """Register a callback to be called when cancellation occurs."""
        if callback not in self._cancel_callbacks:
            self._cancel_callbacks.append(callback)
    
    def register_cleanup_callback(self, callback: Callable[[], None]) -> None:
        """Register a callback to be called during cleanup."""
        if callback not in self._cleanup_callbacks:
            self._cleanup_callbacks.append(callback)
    
    def cleanup(self) -> None:
        """Execute cleanup callbacks."""
        for callback in self._cleanup_callbacks:
            try:
                callback()
            except Exception:
                pass  # Ignore cleanup errors
        self._cleanup_callbacks.clear()
        self._cancel_callbacks.clear()

class CancellationScope:
    """A context manager for managing cancellation tokens."""
    
    def __init__(self, token: Optional[CancellationToken] = None):
        self.token = token or CancellationToken()
    
    async def __aenter__(self) -> CancellationToken:
        return self.token
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self.token.cleanup()
        if exc_type is asyncio.CancelledError and not self.token.is_cancelled:
            # Convert external cancellation to our token
            self.token.cancel() 
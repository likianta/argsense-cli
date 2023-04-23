class Signal:
    
    def __init__(self):
        self._callbacks = {}
    
    def connect(self, callback):
        self._callbacks[id(callback)] = callback
    
    def emit(self, *args, **kwargs):
        for callback in self._callbacks.values():
            callback(*args, **kwargs)

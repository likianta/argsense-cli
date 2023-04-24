from .signal import Signal
from .signal import SignalInit


class Logger(SignalInit):
    streamed = Signal(str)
    
    def log(self, msg: str) -> None:
        self.streamed.emit(msg)


logger = Logger()
log = logger.log

try:
    from .app import run
except ImportError:
    from ._broken import fake_run as run

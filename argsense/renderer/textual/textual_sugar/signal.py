class Signal:
    
    def __init__(self, *_):
        self._callbacks = {}
    
    def __call__(self, *args, **kwargs):
        self.emit(*args, **kwargs)
    
    def connect(self, callback):
        self._callbacks[id(callback)] = callback
    
    def emit(self, *args, **kwargs):
        for callback in self._callbacks.values():
            callback(*args, **kwargs)


class SignalMeta:  # DELETE: not used. turn to `SignalInit`.
    """
    a minxin class for sub-classes to auto create its own signals.
    how to use: see `./widgets.py : class FlatButton`.
    """
    
    def __new__(cls, name, bases, attrs):
        new_attrs = {}
        for k, v in attrs['__annotations__'].items():
            if v is Signal:
                # print('auto create signal', k, ':v')
                new_attrs[k] = Signal()
        if new_attrs:
            attrs.update(new_attrs)
        return type(name, bases, attrs)


class SignalInit:
    """
    usage:
        class MyButton(Button, SignalInit):
            clicked: Signal
            
    wrong usages:
        class Wrong1(SignalInit, Button):
            ...  #   ^^^^^^^^^^ incorrect order
        class Wrong2(Button, SignalInit):
            clicked: Signal()
            #              ^^ instance of Signal
        class Wrong3(Button, SignalInit):
            clicked = Signal()
            #       ^ attribute assignment
    """
    
    def __new__(cls, *_, **__):
        # FIXME: the descendants may behave wrong.
        new_attrs = {}
        for k, v in cls.__dict__.items():
            if isinstance(v, Signal):
                # print('auto create owned signal', k, ':v')
                new_attrs[k] = Signal()
        
        obj = super().__new__(cls)
        if new_attrs: obj.__dict__.update(new_attrs)
        
        return obj

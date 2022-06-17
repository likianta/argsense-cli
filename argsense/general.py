from __future__ import annotations

from typing import Iterable


def did_you_mean(wrong_word: str, known_words: Iterable[str]) -> str | None:
    """ a simple function to find the closest word.
    
    this function is served for the following cases:
        - user types a wrong command name
        - user types a wrong option name
    see also:
        - [./cli.py : def run() : KeyError occurance]
        - [./argparse/parser.py : def parse_argv()]
    
    note: we are using the built-in library - [#1 difflib] - to implement this.
    
    [#1: https://docs.python.org/3/library/difflib.html]
    """
    from difflib import get_close_matches
    if r := get_close_matches(wrong_word, known_words, n=1, cutoff=0.7):
        return str(r[0])
    else:
        return None

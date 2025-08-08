"""
       d8888                  .d8888b.
      d88888                 d88P  Y88b
     d88P888                 Y88b.
    d88P 888 888d888 .d888b.   "Y888b.    .d88b.  88888b.  .d8888b   .d88b.
   d88P  888 888P"  d88P""88b     "Y88b. d8P  Y8b 888 "88b 88K      d8P  Y8b
  d88P   888 888   888    888       "888 88888888 888  888 "Y8888b. 88888888
 d8888888888 888   Y8b    888 Y88b  d88P Y8b.     888  888      X88 Y8b.
d88P     888 888    "Y899888i  "Y8888P"   "Y8888  888  888  88888P'  "Y8888
                          888
                   Y8b    d8P
                    "Y8888P"
"""
if 1:
    import lk_logger
    lk_logger.setup(quiet=True)

from . import config
from . import converter
from . import parser
from .api import run_func
from .cli import CommandLineInterface
from .cli import cli
from .converter import args_2_cargs
from .converter import name_2_cname
from .converter import type_2_ctype
from .parser import parse_argstring
from .parser import parse_argv
from .parser import parse_docstring
from .parser import parse_function

__version__ = '1.1.0'

import os
import sys
from lk_utils import run_cmd_args
os.environ['ARGSENSE_DEBUG'] = '1'
print(sys.argv)
run_cmd_args(
    sys.executable, '-m', 'argsense', '-h',
    verbose=True,
    force_term_color=True,
)

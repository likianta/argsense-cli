import os
os.environ['ARGSENSE_DEBUG'] = '1'

import streamlit as st
from argsense import cli


@cli.cmd()
def main(aaa, bbb) -> None:
    st.write(str(aaa))
    st.write(str(bbb))


if __name__ == '__main__':
    # strun 3001 test/streamlit_run.py -- alpha beta
    cli.run(main)

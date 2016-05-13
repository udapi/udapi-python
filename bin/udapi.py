#!/usr/bin/env python

from udapi.core.run import Run

if __name__ == "__main__":

    runner = Run( command_line_argv = sys.argv )
    runner.execute()

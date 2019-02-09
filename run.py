import sys

from cli import TerminalLogin as Console
from util import paths


paths.chroot(sys.argv[0])
term = Console()

if __name__ == "__main__":
    term.cmdloop()

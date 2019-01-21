import sys

from cli import TerminalLogin as Console
import constructs


def go():
    Console().cmdloop()


if __name__ == "__main__":
    go()

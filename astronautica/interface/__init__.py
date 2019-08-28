"""Interface Package: Command line Client and all integrations with Engine."""

from typing import Tuple

from .client import Client
from .commands import CommandRoot


def get_client() -> Tuple[Client, CommandRoot]:
    interface_client = Client()
    command_system = CommandRoot(interface_client)
    interface_client.handler = command_system.run

    return interface_client, command_system

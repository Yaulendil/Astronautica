working_dir = "/astronautica"
turn_length = 300  # Seconds

cmd_prompt = "{c}{u}@{h}\033[0m:\033[94m{p}\033[0m$ "
cmd_aliases = {"quit": "exit", "logout": "exit"}


class Scan:
    result_none = "Telemetry includes no {}."
    indent=3
    display_attr = ["radius", "mass", "coords"]
    decimals = 3

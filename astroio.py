import json


def load(path):
    with path.open() as content:
        j = json.load(content)
    return j


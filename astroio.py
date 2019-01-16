import json


def load(path):
    with path.open() as file:
        data = json.load(file)
    return data


def save(path, data):
    with path.open("w") as file:
        json.dump(data, file, indent=2)
    return

import json


def load(path):
    with path.with_suffix(".json").resolve().open("r") as file:
        data = json.load(file)
    return data


def save(path, data):
    with path.with_suffix(".json").resolve().open("w") as file:
        json.dump(data, file, indent=2)
    return

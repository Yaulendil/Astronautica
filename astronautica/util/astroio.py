import json

# from util.paths import get_path


def load(path):
    # path = get_path(path)
    with path.with_suffix(".json").open("r") as file:
        data = json.load(file)
    return data


def save(path, data):
    # path = get_path(path)
    with path.with_suffix(".json").open("w") as file:
        json.dump(data, file, indent=2)
    return


def ls(path):
    # path = get_path(path)
    return path.glob("*")

from interface import Client


if __name__ == "__main__":
    with Client() as app:
        app.run()

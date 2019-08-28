from interface import get_client


if __name__ == "__main__":
    client, commands = get_client()

    with client as app:
        app.run()

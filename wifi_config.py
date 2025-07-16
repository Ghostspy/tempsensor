import ujson

def load_config():
    try:
        with open("wifi_config.json") as f:
            return ujson.load(f)
    except:
        return {}

def save_config(ssid, password):
    with open("wifi_config.json", "w") as f:
        ujson.dump({"ssid": ssid, "password": password}, f)

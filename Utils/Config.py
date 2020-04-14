import json

def get_data():
    config = open('cfg.json')
    data = json.load(config)
    config.close()
    return data

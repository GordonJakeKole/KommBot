import json

def get_data():
    config = open('cfg.json', encoding='utf-8')
    data = json.load(config)
    config.close()
    return data

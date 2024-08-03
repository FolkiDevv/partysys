import tomllib

with open('config.toml', 'rb') as config_file:
    CFG = tomllib.load(config_file)

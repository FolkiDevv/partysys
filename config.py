import tomllib

with open('config.toml', 'rb') as config_file:
    CONF = tomllib.load(config_file)

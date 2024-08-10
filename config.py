import os
import sys

import tomllib

if 'unittest' in sys.modules:
    CFG = {}
else:
    with open('config.toml', 'rb') as config_file:
        CFG = tomllib.load(config_file)

TORTOISE_ORM = {
    "connections": {
        "default": f'mysql://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}'
                   f'@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}'
                   f'/{os.getenv("DB_NAME")}'
    },
    "apps": {
        "models": {
            "models": ["src.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}

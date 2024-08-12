# Partysys

<p>
    <img alt="Python version" src="https://img.shields.io/badge/python-3.12-blue?link=https%3A%2F%2Fpython.org">
    <img alt="Static Badge" src="https://img.shields.io/badge/discord.py-%5E2.3.2-green?link=https%3A%2F%2Fgithub.com%2FRapptz%2Fdiscord.py">
</p>

English | [Русский](./README_RU.md)

## Introduction

This is [Discord](https://discord.com) bot with a system of temporary voice channels and live adverts for them.

## Installing

**Python 3.12 or higher is required**

### I. Without Docker
#### 1. Cloning the repository

```shell
git clone https://github.com/FolkiDevv/partysys.git
cd partysys
````

#### 2. Installing dependencies

> [!IMPORTANT]
> This project use [Poetry](https://python-poetry.org/) for dependency management.

```shell
poetry install --only main --no-interaction
````

#### 3. Setting up the environment variables

You can find all the necessary environment variables in the file [`docker-compose.yml`](./docker-compose.yml).

#### 4. Applying the migrations

Project uses [Tortoise ORM](https://tortoise.github.io) for database management and [Aerich](https://github.com/tortoise/aerich) for migrations.

To apply the migrations, run the following command:
```shell
aerich upgrade
```

#### 5. Running the bot
```shell
poetry run python main.py
```

### II. Using Docker

Docker images are available on [ghcr.io](https://ghcr.io/folkidevv/partysys).

When pushing to the `master` branch, the image is automatically built and pushed to the registry.
```shell
docker pull ghcr.io/folkidevv/partysys:master
```

## Contributing

This is an open-source project, and we welcome contributions from the community.
If you'd like to contribute, please fork the repository and make changes as you'd like. Pull requests are warmly welcome.

> [!IMPORTANT]
> Please make sure that your changes pass the [Ruff](https://docs.astral.sh/ruff/) linter check by configuration in `pyproject.toml`.

## License

This project is licensed under the terms of the MIT license.
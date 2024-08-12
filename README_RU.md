# Partysys

<p>
    <img alt="Python version" src="https://img.shields.io/badge/python-3.12-blue?link=https%3A%2F%2Fpython.org">
    <img alt="Static Badge" src="https://img.shields.io/badge/discord.py-%5E2.3.2-green?link=https%3A%2F%2Fgithub.com%2FRapptz%2Fdiscord.py">
</p>

[English](./README.md) | Русский

## Введение

Это [Discord](https://discord.com) бот с системой временных голосовых каналов и "живой" рекламой для них.

## Установка

**Необходим Python 3.12 и выше**

### I. Без использования Docker
#### 1. Клоинрование репозитория

```shell
git clone https://github.com/FolkiDevv/partysys.git
cd partysys
````

#### 2. Установка зависимостей

> [!IMPORTANT]
> Проект использует [Poetry](https://python-poetry.org/) для управления зависимостями.

```shell
poetry install --only main --no-interaction
````

#### 3. Настройка переменных окружения

Все необходимые для работы переменные окружения можно найти в файле [`docker-compose.yml`](./docker-compose.yml).

#### 4. Применение миграций

В проекте используется [Tortoise ORM](https://tortoise.github.io) и [Aerich](https://github.com/tortoise/aerich) для миграций.

Чтобы применить миграции, выполните следующую команду:
```shell
aerich upgrade
```

#### 5. Запуск бота
```shell
poetry run python main.py
```

### II. С использованием Docker

Образы Docker доступны на [ghcr.io](https://ghcr.io/folkidevv/partysys).

При обновлениях в ветке `master` образ автоматически собирается и размещается в реестре.
```shell
docker pull ghcr.io/folkidevv/partysys:master
```

## Contributing

Это open-source проект, и мы приветствуем вклады от сообщества.
Если вы хотите внести свой вклад, пожалуйста, сделайте форк репозитория и внесите изменения по своему усмотрению. Pull requests приветствуются.

> [!IMPORTANT]
> Пожалуйста убедитесь что ваши изменения проходят проверку [Ruff](https://docs.astral.sh/ruff/) линтером с конфигурацией из `pyproject.toml`.

## Лицензия

Этот проект лицензирован на условиях лицензии MIT.
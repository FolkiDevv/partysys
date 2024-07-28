# Use multi-stage builds
# First stage: builder
FROM python:3.12-slim-bullseye as builder

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  # Poetry's configuration:
  POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry' \
  POETRY_HOME='/usr/local'

# Install Poetry
RUN python -m pip install --no-cache-dir poetry \
  # Cleaning cache:
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy only requirements to cache them in docker layer
COPY poetry.lock pyproject.toml /app/

# Install dependencies
RUN poetry install --only=main --no-interaction --no-ansi

# Copy the rest of the code
COPY . /app

# Second stage: runtime
FROM python:3.12-slim-bullseye as runtime

# Create app user and group
RUN addgroup --gid 1001 --system app && \
    adduser --no-create-home --shell /bin/false  \
    --disabled-password --uid 1001 --system --group app

# Set work directory
WORKDIR /app

# Copy installed dependencies from the builder image
COPY --from=builder /app /app

# Switch to the app user
USER app

# Set environment variables
ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PYTHONDONTWRITEBYTECODE=1 \
  # pip:
  PIP_NO_CACHE_DIR=1 \
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  PIP_DEFAULT_TIMEOUT=100 \
  PIP_ROOT_USER_ACTION=ignore

# Set the entrypoint
ENTRYPOINT ["python", "-m", "main"]
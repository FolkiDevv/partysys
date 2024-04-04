FROM python:3.12-slim-bullseye as builder

# Install poetry
RUN pip install poetry

# Configure poetry
RUN poetry config virtualenvs.create true
RUN poetry config virtualenvs.in-project true

# Copy only requirements to cache them in docker layer
WORKDIR /app
COPY poetry.lock pyproject.toml /app/

# Install dependencies
RUN poetry install --only main --no-interaction --no-ansi --no-root

COPY . /app

FROM python:3.12-slim-bullseye as runtime

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PYTHONDONTWRITEBYTECODE=1 \
  # pip:
  PIP_NO_CACHE_DIR=1 \
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  PIP_DEFAULT_TIMEOUT=100 \
  PIP_ROOT_USER_ACTION=ignore

# Copy installed dependencies from the builder image
COPY --from=builder /app /app

WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"

#ENTRYPOINT ["python", "-m", "main"]
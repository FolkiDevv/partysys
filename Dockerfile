FROM python:3.12-slim-bullseye as builder

# Install Poetry
RUN pip install poetry

# Copy only requirements to cache them in docker layer
WORKDIR /app
COPY poetry.lock pyproject.toml /app/

# Configure Poetry and Install dependencies
RUN poetry config virtualenvs.create true &&  \
    poetry config virtualenvs.in-project true &&  \
    poetry install --only main --no-interaction --no-ansi --no-root

COPY . /app

FROM python:3.12-slim-bullseye as runtime
RUN addgroup --gid 1001 --system app && \
    adduser --no-create-home --shell /bin/false --disabled-password --uid 1001 --system --group app

# Create logs directory as root and change its ownership to app user
USER root
RUN mkdir -p /app/logs && chown -R app:app /app/logs && chmod -R 755 /app/logs

# Switch back to app user
USER app

# Copy installed dependencies from the builder image
COPY --chown=app:app --from=builder /app /app

WORKDIR /app

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PYTHONDONTWRITEBYTECODE=1 \
  # pip:
  PIP_NO_CACHE_DIR=1 \
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  PIP_DEFAULT_TIMEOUT=100 \
  PIP_ROOT_USER_ACTION=ignore \
  PATH="/app/.venv/bin:$PATH"

ENTRYPOINT ["python", "-m", "main"]
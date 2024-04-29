# Use multi-stage builds
# First stage: builder
FROM python:3.12-slim-bullseye as builder

# Install UV
RUN pip install uv

# Set work directory
WORKDIR /app

# Copy only requirements to cache them in docker layer
COPY README.md pyproject.toml /app/

# Install dependencies
RUN uv pip compile pyproject.toml -o requirements.txt && \
    uv venv && \
    uv pip install -r requirements.txt

# Copy the rest of the code
COPY . /app

# Second stage: runtime
FROM python:3.12-slim-bullseye as runtime

# Create app user and group
RUN addgroup --gid 1001 --system app && \
    adduser --no-create-home --shell /bin/false --disabled-password --uid 1001 --system --group app

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
  PIP_NO_CACHE_DIR=1 \
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  PIP_DEFAULT_TIMEOUT=100 \
  PIP_ROOT_USER_ACTION=ignore \
  PATH="/app/.venv/bin:$PATH"

# Set the entrypoint
ENTRYPOINT ["python", "-m", "main"]
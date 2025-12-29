##### Base Stage #####
FROM ubuntu:24.04 AS base

# Set default path
ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONPATH="/app"
ENV UV_PYTHON_INSTALL_DIR="/app/"

##### Builder Stage #####
FROM base AS builder

# Set default workdir
WORKDIR /app

# Create virtualenv and install Python packages
COPY --from=docker.io/astral/uv:latest /uv /bin/
COPY ./uv.lock uv.lock
COPY ./pyproject.toml pyproject.toml
RUN uv sync --no-dev --frozen

# Copy app files to workdir
COPY fastpubsub ./fastpubsub
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations

# Compile all Python source files to bytecode
RUN python -m compileall -f .

##### Final Stage #####
FROM base

# Copy content from builder stage
COPY --from=builder /app /app

# Add app user and create directories
RUN useradd -m app

# Set permissions
RUN chown -R app:app /app

# Set workdir and user
WORKDIR /app
USER app

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["python", "fastpubsub/main.py"]

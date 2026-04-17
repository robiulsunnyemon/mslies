# Base Image
FROM python:3.11-slim AS python-base

# ENV variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.8.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:/app/.venv/bin:$PATH"

# Build dependencies
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        curl \
        build-essential

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set working directory
WORKDIR /app

# Copy dependency files first for caching
COPY pyproject.toml ./
# If poetry.lock already exists, copy it too
COPY poetry.lock* ./

# Install dependencies (runtime only)
RUN poetry install --no-root

# Copy project files
COPY . .

# Generate Prisma Client
RUN poetry run prisma generate

# Final staging
EXPOSE 8000

# Start command
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

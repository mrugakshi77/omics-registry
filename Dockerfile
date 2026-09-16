FROM ubuntu:24.04

# Install curl (needed to install pixi) and clean up apt cache to keep the image small
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install pixi itself
RUN curl -fsSL https://pixi.sh/install.sh | bash
ENV PATH="/root/.pixi/bin:${PATH}"

WORKDIR /app

# Copy only dependency-defining files first -- this is a deliberate layer-
# caching trick: Docker only re-runs `pixi install` (the slow step) when
# these specific files change, not every time you edit application code.
COPY pixi.toml pixi.lock pyproject.toml README.md ./
COPY alembic.ini ./
COPY alembic ./alembic
COPY scripts ./scripts
COPY data ./data
COPY src ./src

RUN pixi install --locked

EXPOSE 8000

CMD ["pixi", "run", "uvicorn", "omics_registry.main:app", "--host", "0.0.0.0", "--port", "8000"]

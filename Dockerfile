# syntax=docker/dockerfile:1
# Agent Doorway gateway image: two stages so the runtime image has no build tools.

# ---- build: resolve and install dependencies with uv -----------------------
FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
# Dependencies first (cached layer), then the project itself.
COPY pyproject.toml uv.lock README.md LICENSE ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev

# ---- runtime: just Python, the virtualenv and a non-root user --------------
FROM python:3.12-slim AS runtime
RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin doorway
WORKDIR /app
COPY --from=build --chown=doorway:doorway /app /app
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER doorway
EXPOSE 8080
# The slim image has no curl, so the healthcheck uses the Python standard library.
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=2).status == 200 else 1)"]
CMD ["doorway", "serve", "--host", "0.0.0.0", "--port", "8080"]

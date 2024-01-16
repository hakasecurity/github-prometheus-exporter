FROM python:3.11-slim AS prod

ENV POETRY_CACHE_DIR=/tmp/poetry_cache
ENV POETRY_VIRTUALENVS_PATH=/tmp/poetry_virtualenvs

RUN pip install poetry>=1.2.2


WORKDIR /app

RUN groupadd -r haka && useradd --no-log-init -r -m -g haka haka

RUN mkdir -p github_prometheus_exporter/github_prometheus_exporter && chown -R haka:haka github_prometheus_exporter/
WORKDIR /app/github_prometheus_exporter

# Poetry requires both files in order to install deps.
RUN touch github_prometheus_exporter/__init__.py README.md

COPY --chown=haka:haka pyproject.toml poetry.lock ./

USER haka

RUN poetry install

COPY --chown=haka github_prometheus_exporter /app/github_prometheus_exporter/github_prometheus_exporter

CMD ["poetry", "run", "python", "-m", "github_prometheus_exporter"]
FROM docker.io/library/python:3.12-slim

WORKDIR /app

COPY uv.lock pyproject.toml ./

RUN pip install --upgrade pip && \
    pip install uv && \
    uv pip install --system -r pyproject.toml 


COPY ./ ./

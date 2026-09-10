FROM python:3.11-slim AS builder

WORKDIR /build

RUN pip install --no-cache-dir build

COPY pyproject.toml .
COPY veni/ veni/

RUN python -m build --wheel

FROM python:3.11-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl

RUN useradd -m -u 1000 veni
USER veni

ENV HOME=/home/veni

ENTRYPOINT ["veni"]
CMD ["chat"]

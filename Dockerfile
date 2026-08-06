# syntax=docker/dockerfile:1
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ffmpeg \
       exiftool \
       mediainfo \
       tini \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 10001 forensic \
    && useradd --uid 10001 --gid forensic --create-home forensic

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install .

USER forensic
ENTRYPOINT ["/usr/bin/tini", "--", "video-forensics"]
CMD ["--help"]

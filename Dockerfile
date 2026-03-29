FROM debian:trixie-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        cmake \
        git \
        libcapstone-dev \
        libicu-dev \
        ninja-build \
        pkg-config \
        python3 \
        python3-pyelftools \
        python3-requests \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app

RUN mkdir -p /work

ENTRYPOINT ["python3", "/app/blutter.py"]
CMD ["--help"]

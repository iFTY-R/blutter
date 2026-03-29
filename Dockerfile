FROM debian:trixie-slim

ARG PREBUILD_TARGETS=""
ARG PREBUILD_DEFAULT_OS="android"
ARG PREBUILD_DEFAULT_ARCH="arm64"
ARG PREBUILD_WITH_NO_ANALYSIS="0"
ARG PREBUILD_COMPRESSED_PTRS="1"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PREBUILD_TARGETS=${PREBUILD_TARGETS}
ENV PREBUILD_DEFAULT_OS=${PREBUILD_DEFAULT_OS}
ENV PREBUILD_DEFAULT_ARCH=${PREBUILD_DEFAULT_ARCH}
ENV PREBUILD_WITH_NO_ANALYSIS=${PREBUILD_WITH_NO_ANALYSIS}
ENV PREBUILD_COMPRESSED_PTRS=${PREBUILD_COMPRESSED_PTRS}

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

RUN if [ -n "$PREBUILD_TARGETS" ]; then python3 /app/scripts/docker_prebuild.py; fi

RUN mkdir -p /work

ENTRYPOINT ["python3", "/app/blutter.py"]
CMD ["--help"]

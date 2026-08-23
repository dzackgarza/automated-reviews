FROM oven/bun:1.2.22@sha256:66ba69deede44e3af5dc542def218fdb3bcad2205900ea761dc5623bf973d2df AS bun
FROM ghcr.io/astral-sh/uv:0.12.5@sha256:e85be844203885286c60ffad8a858d48afb6c5a5c237ca0e67f12e74b8f174b1 AS uv
FROM ghcr.io/catthehacker/ubuntu:act-24.04@sha256:62d572b92f9f32d3427b6d220ad1f9dca9c7b6ffad37d295425037dbff78abaf

COPY --from=bun /usr/local/bin/bun /usr/local/bin/bun
COPY --from=uv /uv /uvx /usr/local/bin/

RUN apt-get update \
    && apt-get install --yes --no-install-recommends rsync trash-cli \
    && apt-get clean \
    && trash-put /var/lib/apt/lists/*

RUN curl --fail --location --silent --show-error \
      https://github.com/casey/just/releases/download/1.58.0/just-1.58.0-x86_64-unknown-linux-musl.tar.gz \
      --output /tmp/just.tar.gz \
    && printf '%s  %s\n' \
      4a5cc2f53e6f0f8c59092a6cc38291eb729d46a7dd95d3ae582008881b84931d \
      /tmp/just.tar.gz | sha256sum --check \
    && tar --extract --gzip --file /tmp/just.tar.gz --directory /usr/local/bin just \
    && trash-put /tmp/just.tar.gz

RUN bun add --global opencode-ai@1.18.21 cc-safety-net@2.0.11 \
    && install "$(readlink -f /root/.bun/bin/opencode)" /usr/local/bin/opencode \
    && install "$(readlink -f /root/.bun/bin/cc-safety-net)" /usr/local/bin/cc-safety-net

CMD ["sleep", "infinity"]

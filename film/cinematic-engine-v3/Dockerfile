# Native 2D Hunyuan cinematic renderer. NOT a 3D character engine.
# Pinned Node 22 + exact JS versions from the successful approved 30-second pilot.
# Build once/publish to GHCR, reuse across all rendering runners.
FROM node:22-bookworm-slim
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PATH=/opt/cinematic/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-pip python3-venv ffmpeg unzip ca-certificates \
      git fontconfig fonts-dejavu-core fonts-liberation tini \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/cinematic
COPY film/cinematic-engine-v3/requirements.txt /opt/cinematic/requirements.txt
RUN python3 -m venv /opt/cinematic/venv \
    && pip install --no-cache-dir -r /opt/cinematic/requirements.txt
COPY film/cinematic-engine-v3/package.json /opt/cinematic/package.json
RUN npm install --include=dev --no-audit --no-fund \
    && npx playwright install --with-deps chromium
COPY film/cinematic-engine-v3/ /opt/cinematic/engine/
COPY film/hunyuan-2m/HUNYUAN_2D_CHARACTER_PACKAGE.zip /opt/cinematic/references/HUNYUAN_2D_CHARACTER_PACKAGE.zip
COPY film/hunyuan-2m/HUNYUAN_30S_PARALLAX_SOURCE.zip /opt/cinematic/references/HUNYUAN_30S_PARALLAX_SOURCE.zip
# This is the real, already-approved video downloaded from GitHub Actions run #44029412483
# before docker build. It is not regenerated and permanently lives inside the GHCR image.
COPY film/cinematic-engine-v3/reference_input/HUNYUAN_FIRST_30S_PARALLAX_PREVIEW.mp4 /opt/cinematic/references/HUNYUAN_FIRST_30S_PARALLAX_PREVIEW.mp4
# Source instructions are copied UNCHANGED; SHA256 checks must pass or build fails.
RUN python3 /opt/cinematic/engine/scripts/doctor.py --check
ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["python3","/opt/cinematic/engine/scripts/doctor.py","--check"]

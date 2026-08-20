# Build-only image. The application itself never runs inside Docker in
# production — this image exists solely to freeze the app/helper with
# PyInstaller and assemble the .deb, using the same Ubuntu version as the
# target lab machines (24.04 LTS) so the frozen gi._gi extension's ABI
# matches what it will dlopen at runtime on those machines.
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3 \
    python3-dev \
    python3-venv \
    python3-pip \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-4.0 \
    gir1.2-adw-1 \
    libgirepository1.0-dev \
    pkg-config \
    fakeroot \
    dpkg-dev \
    && rm -rf /var/lib/apt/lists/*

# PyGObject itself comes from apt (python3-gi) above, linked against this
# image's exact glib/gobject — never installed via pip, which would build
# against whatever headers happen to be present and risk an ABI mismatch
# with the system libs the frozen app will dlopen at runtime.
COPY requirements.txt /tmp/requirements.txt
RUN pip install --break-system-packages --no-cache-dir -r /tmp/requirements.txt

WORKDIR /build
COPY . /build

RUN chmod +x packaging/build-deb.sh packaging/pyinstaller/build.sh docker/build.sh

ENTRYPOINT ["docker/build.sh"]

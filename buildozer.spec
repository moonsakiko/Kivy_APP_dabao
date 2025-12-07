name: Stable Build
on:
  workflow_dispatch:

jobs:
  build:
    # 使用 Ubuntu 20.04 或 22.04，这两个版本编译 Python 最稳
    runs-on: ubuntu-22.04

    steps:
      - name: Checkout
        uses: actions/checkout@v3

      # 1. 清理磁盘 (必须，否则编译到一半空间不足)
      - name: Free Disk Space
        uses: jlumbroso/free-disk-space@main
        with:
          tool-cache: false
          android: true
          dotnet: true
          haskell: true
          large-packages: true
          swap-storage: true

      # 2. 手动安装依赖 (比第三方Action更稳)
      - name: Install System Dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            build-essential \
            libltdl-dev \
            libffi-dev \
            libssl-dev \
            python3-dev \
            python3-setuptools \
            zip \
            unzip \
            autoconf \
            libtool \
            pkg-config \
            zlib1g-dev \
            libncurses5-dev \
            libncursesw5-dev \
            libtinfo5 \
            cmake \
            libffi-dev

      # 3. 安装 Buildozer
      - name: Install Buildozer
        run: |
          pip3 install --upgrade pip
          pip3 install buildozer cython==0.29.36

      # 4. 开始打包 (yes | ... 自动同意SDK协议)
      # 这里加 verbose 可以在 Github 后台看到详细日志
      - name: Build APK
        run: |
          yes | buildozer android debug verbose

      # 5. 上传
      - name: Upload Artifact
        uses: actions/upload-artifact@v4
        with:
          name: app-debug
          path: bin/*.apk

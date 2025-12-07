[app]
title = My Stable App
package.name = myapp
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 1.0

# ❗❗❗ 核心修改区 ❗❗❗
# 1. 加上 typing-extensions (pypdf 必崩之源)
# 2. 加上 pillow (图片处理必须)
# 3. 加上 certifi (SSL证书，虽然你可能没用，加上防报错)
# 4. 指定 kivy 版本以防版本冲突
requirements = python3, kivy==2.2.1, pypdf, pillow, typing-extensions, certifi, idna, charset-normalizer, urllib3, android

# 屏幕方向
orientation = portrait
fullscreen = 0

# 权限 (注意：安卓10+ 需要在 main.py 里动态申请)
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# 安卓 API 配置 (保持稳定)
android.api = 33
android.minapi = 21
android.ndk_api = 21

# 架构 (现在的手机基本都是 arm64-v8a，但也加上 v7a 兼容旧手机)
android.archs = arm64-v8a, armeabi-v7a

# 启动图优化 (防止启动白屏太久)
android.presplash_color = #000000

[buildozer]
log_level = 2
warn_on_root = 1

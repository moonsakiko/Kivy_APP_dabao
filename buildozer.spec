[app]
title = PDF Master Pro
package.name = pdfmasterpro
package.domain = org.master
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 14.0

# ❗升级回 Kivy 2.3.0，享受流畅体验
requirements = python3, kivy==2.3.0, pypdf, pillow, android

# ❗开启双架构，彻底根治白屏
android.archs = arm64-v8a, armeabi-v7a

# 启用自定义图片（如果你仓库里有这两个文件，就取消注释，否则保持注释）
# icon.filename = icon.png
# presplash.filename = presplash.png

# 启动图背景色：纯白
android.presplash_color = #FFFFFF

orientation = portrait
fullscreen = 0
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.ndk_api = 21

[buildozer]
log_level = 2
warn_on_root = 1

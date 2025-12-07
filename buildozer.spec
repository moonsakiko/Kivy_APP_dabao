[app]
title = PDF Master
package.name = pdfmaster
package.domain = org.master
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 10.0

# ❗依赖：只保留最核心的
requirements = python3, kivy==2.3.0, pypdf, pillow, android

# ❗暂时注释掉自定义图片，排除干扰
# icon.filename = icon.png
# presplash.filename = presplash.png

# 保持白色背景，视觉上快
android.presplash_color = #FFFFFF

orientation = portrait
fullscreen = 0
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.ndk_api = 21
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1

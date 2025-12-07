[app]
title = PDF Master Debug
package.name = pdfmasterdebug
package.domain = org.master
source.dir = .
# ❗只包含最基础的后缀，确保 clean
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 11.0

# ❗关键回退：Kivy 2.2.0 (最稳版本)
# ❗移除了 pillow，减少崩溃源
requirements = python3, kivy==2.2.0, pypdf, android

# 保持默认图标，排除图片错误干扰
# icon.filename = icon.png
# presplash.filename = presplash.png

orientation = portrait
fullscreen = 0
android.presplash_color = #FFFFFF

android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.ndk_api = 21
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1

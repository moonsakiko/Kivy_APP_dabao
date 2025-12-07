[app]
title = PDF Tool Final
package.name = pdftoolfinal
package.domain = org.final
source.dir = .
# ❗关键：一定要包含 ttf
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 5.0

# ❗关键：剔除 kivymd，只用稳如泰山的 kivy 2.2.0
requirements = python3, kivy==2.2.0, pypdf, pillow, android

orientation = portrait
fullscreen = 0
# 启动图改为深灰色，看起来高级点
android.presplash_color = #222222

# 权限
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.ndk_api = 21
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1

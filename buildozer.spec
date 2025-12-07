[app]
title = PDF Master
package.name = pdfmaster
package.domain = org.master
source.dir = .
# 记得保留 ttf
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 7.0

# ❗❗❗ 核心修改：增加了 plyer 库 ❗❗❗
requirements = python3, kivy==2.3.0, pypdf, pillow, plyer, android

orientation = portrait
fullscreen = 0
android.presplash_color = #FFFFFF

# 权限 (plyer 需要读写权限)
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.ndk_api = 21
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1

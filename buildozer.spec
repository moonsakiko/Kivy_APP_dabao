[app]
title = PDF Master
package.name = pdfmaster
package.domain = org.master
source.dir = .
# 记得保留 ttf
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 8.0

# ❗依赖：去掉 plyer，我们用更底层的 android
requirements = python3, kivy==2.3.0, pypdf, pillow, android

orientation = portrait
fullscreen = 0

# ❗美化启动页：设为极简白，跟APP背景融为一体，产生“秒开”的错觉
android.presplash_color = #F5F5F7

# 权限
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.ndk_api = 21
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1

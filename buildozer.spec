[app]
title = PDF Master Debug
package.name = pdfmasterdebug
package.domain = org.master
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 12.0

# ❗移除 pillow，保留最简依赖
requirements = python3, kivy==2.2.0, pypdf, android

# ❗暂时注释掉图片，先跑通代码
# icon.filename = icon.png
# presplash.filename = presplash.png

orientation = portrait
fullscreen = 0
android.presplash_color = #FFFFFF

android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.ndk_api = 21

# ❗❗❗ 极速编译修改：只打包 64 位架构 ❗❗❗
# 这会让打包速度快一倍，且绝大多数现代手机都能装
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1

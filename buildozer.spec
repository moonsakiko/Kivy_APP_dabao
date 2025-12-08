[app]
title = PDF Master Safe
package.name = pdfmastersafe
package.domain = org.master
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 13.0

# ❗依赖：标准稳定版
requirements = python3, kivy==2.2.0, pypdf, android

# ❗架构：改回双架构，牺牲体积换取绝对稳定
android.archs = arm64-v8a, armeabi-v7a

# 启动图颜色：改回黑色，方便区分白屏是不是因为APP没加载
android.presplash_color = #000000

orientation = portrait
fullscreen = 0
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.ndk_api = 21

[buildozer]
log_level = 2
warn_on_root = 1

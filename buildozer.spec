[app]
title = PDF Tool Pro
package.name = pdftoolpro
package.domain = org.pro
source.dir = .
# ❗关键：加入 ttf 后缀，否则字体不会被打包
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 4.0

# ❗关键配合：Kivy 2.2.0 (稳) + KivyMD 1.1.1 (美)
requirements = python3, kivy==2.2.0, kivymd==1.1.1, pypdf, pillow, android

orientation = portrait
fullscreen = 0
# 启动图颜色改为 KivyMD 的深蓝色，显得专业
android.presplash_color = #1E1E1E

# 权限
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.ndk_api = 21
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1

[app]
title = PDF Master
package.name = pdfmaster
package.domain = org.master
source.dir = .
# ❗关键：一定要包含 ttf, png
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 9.0

# ❗依赖
requirements = python3, kivy==2.3.0, pypdf, pillow, android

# ❗自定义图标与开屏配置
# 只要你把图片放对了名字，这里就会自动生效
icon.filename = icon.png
presplash.filename = presplash.png

# ❗开屏背景色
# 如果你的开屏图不是全屏填满的，边缘显示的颜色。设为白色最稳。
android.presplash_color = #FFFFFF

orientation = portrait
fullscreen = 0

# 权限
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.ndk_api = 21
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1

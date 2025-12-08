[app]

# APP 标题
title = 图片压缩工坊

# 包名
package.name = itoolimage
package.domain = org.itool

# 源码目录
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf

# 版本
version = 4.0

# ❗❗❗ 核心依赖 ❗❗❗
# pillow 用于图片处理
requirements = python3, kivy==2.3.0, pillow, android

# 架构 (推荐仅编译 64位 以优化体积)
android.archs = arm64-v8a

# 屏幕方向
orientation = portrait
fullscreen = 0

# ❗❗❗ 权限设置 ❗❗❗
# 需要写文件到 Download 目录
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# 图标设置 (请确保文件存在，否则会报错)
icon.filename = icon.png
presplash.filename = presplash.png
# 启动图背景色 (与APP背景一致，实现无缝启动)
android.presplash_color = #F2F3F7

# API 版本 (Android 13+)
android.api = 33
android.minapi = 21

[buildozer]
log_level = 2
warn_on_root = 1

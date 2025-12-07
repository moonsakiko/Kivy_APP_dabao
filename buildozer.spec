[app]

# App名称
title = PDF合并切割
package.name = pdftoolbox
package.domain = org.example

# 源代码位置
source.dir = .
source.include_exts = py,png,jpg,kv,atlas

# 版本
version = 1.0

# ❗关键依赖配置：包含界面库和PDF库
requirements = python3, kivy==2.3.0, kivymd==1.1.1, pypdf, pillow

# 屏幕方向
orientation = portrait

# ❗权限配置：必须要读写权限才能处理文件
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# Android API 设置 (保持兼容性)
android.api = 33
android.minapi = 21
android.ndk_api = 21

# 是否全屏
fullscreen = 0

# 架构 (Github Actions云打包可以全选)
android.archs = arm64-v8a, armeabi-v7a

# 启动图不需要单独配置，默认黑色

[buildozer]
log_level = 2
warn_on_root = 1

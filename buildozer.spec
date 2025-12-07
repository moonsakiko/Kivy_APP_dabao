[app]
# 1. 基本信息
title = PDF Tool Simple
package.name = pdftoolsimple
package.domain = org.simple
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 3.0

# 2. ❗❗❗ 核心修改：移除 kivymd，Kivy 降级到 2.2.0 ❗❗❗
requirements = python3, kivy==2.2.0, pypdf, pillow, android

# 3. 屏幕设置
orientation = portrait
fullscreen = 0
android.presplash_color = #000000

# 4. 权限 (只保留最基础的)
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# 5. API 版本
android.api = 33
android.minapi = 21
android.ndk_api = 21
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1

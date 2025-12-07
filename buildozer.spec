[app]
title = PDF ToolBox
package.name = pdftoolbox
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.1

# ❗关键修改1：锁定更稳定的版本，加入 pil 和 typing-extensions
requirements = python3, kivy==2.3.0, kivymd==1.1.1, pypdf, pillow, typing-extensions, android

orientation = portrait

# ❗关键修改2：加入 MANAGE_EXTERNAL_STORAGE (全文件访问权限)
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.ndk_api = 21
fullscreen = 0
android.archs = arm64-v8a, armeabi-v7a

# 修复启动白屏过久的问题
android.presplash_color = #FFFFFF

[buildozer]
log_level = 2
warn_on_root = 1

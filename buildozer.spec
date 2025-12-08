[app]
# 1. APP 信息
title = PDF Master Ultra
package.name = pdfmasterultra
package.domain = org.master
source.dir = .
# 包含所有资源
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 15.0

# 2. 依赖 (保持 Kivy 2.3.0 的高性能)
requirements = python3, kivy==2.3.0, pypdf, pillow, android

# 3. ❗架构：开启极速模式 (只打 64 位包)
# 既然代码修复了，我们再次挑战这个选项，追求极致体积
android.archs = arm64-v8a

# 4. 自定义图片 (既然你测试通过了，就开启它)
icon.filename = icon.png
presplash.filename = presplash.png

# 5. 启动图背景 (白色，实现无缝启动)
android.presplash_color = #FFFFFF

# 6. 其他标准设置
orientation = portrait
fullscreen = 0
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.ndk_api = 21

[buildozer]
log_level = 2
warn_on_root = 1

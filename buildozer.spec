[app]
# 1. APP 信息
title = PDF Master
package.name = pdfmaster
package.domain = org.master
source.dir = .
# ❗一定要包含 ttf 字体文件
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 6.0

# 2. ❗❗❗ 核心升级：Kivy 2.3.0 ❗❗❗
# 去掉了 kivymd，加入了 standard library 依赖
requirements = python3, kivy==2.3.0, pypdf, pillow, android

# 3. 界面设置
orientation = portrait
fullscreen = 0
# 启动图颜色：深空灰
android.presplash_color = #212121

# 4. 权限 (基础权限)
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# 5. Android API (Kivy 2.3.0 建议用 API 33+)
android.api = 33
android.minapi = 21
android.ndk_api = 21
android.archs = arm64-v8a, armeabi-v7a

# 6. 优化设置 (减少日志输出，防止 GitHub 报错截断)
[buildozer]
log_level = 1
warn_on_root = 1

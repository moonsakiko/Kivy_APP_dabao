[app]

# 1. 基本信息
title = PDF ToolBox
package.name = pdftoolbox
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas

# 2. 版本号
version = 2.0

# 3. ❗❗❗ 核心依赖 (这是最关键的一行) ❗❗❗
# 增加了 openssl, freetype 等底层库，防止因缺库闪退
requirements = python3, kivy==2.3.0, kivymd==1.1.1, pypdf, pillow, typing-extensions, android, openssl, freetype

# 4. 屏幕与显示
orientation = portrait
fullscreen = 0
# 启动白屏颜色设为白色
android.presplash_color = #FFFFFF

# 5. ❗权限设置 (只保留基础权限，去掉 MANAGE_EXTERNAL_STORAGE 防止兼容性崩溃)
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# 6. Android API 版本 (保持主流稳定)
android.api = 33
android.minapi = 21
android.ndk_api = 21

# 7. 架构 (包含主流架构)
android.archs = arm64-v8a, armeabi-v7a

# 8. 其他设置
# 不要在启动时自动解压 heavy 资源，防止超时
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1

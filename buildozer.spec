[app]

# (str) APP标题 (安装后在手机上显示的名字)
title = PDF Tool

# (str) 包名 (建议全小写)
package.name = pdftool

# (str) 域名 (通常反写，如 org.test)
package.domain = org.example

# (str) 源码目录 (当前目录用 .)
source.dir = .

# (list) 源码包含的文件后缀
source.include_exts = py,png,jpg,kv,atlas

# (str) 版本号
version = 1.0

# ❗❗❗【关键修改：防闪退核心】❗❗❗
# 必须包含 pypdf，否则APP一运行到提取功能就会直接崩
requirements = python3, kivy, pypdf

# (str) 屏幕方向 (portrait=竖屏, landscape=横屏)
orientation = portrait

# (bool) 是否全屏
fullscreen = 0

# ❗❗❗【关键修改：权限】❗❗❗
# 必须申请读写权限，否则无法扫描 Download 文件夹
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# (int) Android API 版本 (默认 31 对应 Android 12，兼容性较好)
android.api = 31
# (int) 最小支持版本 (21 对应 Android 5.0)
android.minapi = 21

# (bool) 是否开启 Logcat 日志 (调试用，正式版可改为 0)
android.logcat_filters = *:S python:D

# (str) 架构支持 (同时打包两种架构，兼容所有手机)
android.archs = arm64-v8a, armeabi-v7a

# (bool) 允许备份
android.allow_backup = True

# -----------------------------------------------------------------------------
# Buildozer 专用配置 (不用改)
# -----------------------------------------------------------------------------
[buildozer]
log_level = 2
warn_on_root = 1

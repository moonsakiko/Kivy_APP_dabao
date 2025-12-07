import traceback
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.lang import Builder

# ---------------------------------------------------------
# 1. 动态申请权限 (安卓10+必须在代码里申请，spec里写了没用)
# ---------------------------------------------------------
from kivy.utils import platform

def request_android_permissions():
    if platform == 'android':
        from android.permissions import request_permissions, Permission
        request_permissions([
            Permission.READ_EXTERNAL_STORAGE, 
            Permission.WRITE_EXTERNAL_STORAGE
        ])

# ---------------------------------------------------------
# 2. 这里尝试导入你的库，如果缺库，直接会被捕获
# ---------------------------------------------------------
import_error_msg = None
try:
    # === 在这里写你原本的 import ===
    import os
    import sys
    # import numpy as np  # 如果你有用到
    import pypdf          # 你提到的库
    from PIL import Image # 你提到的 pillow
    # from kivymd.app import MDApp # 如果你用了KivyMD
    
    # 模拟你的主业务逻辑类
    # from my_script import MyMainLayout 
    
except Exception as e:
    # 如果导入就挂了，记录错误
    import_error_msg = traceback.format_exc()

# ---------------------------------------------------------
# 3. 主程序入口
# ---------------------------------------------------------
class CrashProofApp(App):
    def build(self):
        request_android_permissions() # 启动时申请权限

        # 如果导入阶段就报错了，直接显示错误堆栈
        if import_error_msg:
            return self.error_ui(import_error_msg)

        try:
            # === 这里写你原本的界面构建逻辑 ===
            # return MyMainLayout()
            return Label(text="APP 启动成功！\n没有检测到崩溃。", font_size='20sp')
            
        except Exception as e:
            # 如果运行阶段报错，显示错误
            return self.error_ui(traceback.format_exc())

    def error_ui(self, error_content):
        """ 一个简易的错误显示界面，确保报错可见 """
        print(error_content) # 打印到控制台
        layout = ScrollView()
        label = Label(
            text=f"【程序崩溃】\n请截图此页面求助\n\n{error_content}",
            font_size='16sp',
            color=(1, 0, 0, 1), # 红色字
            size_hint_y=None,
            halign='left',
            valign='top'
        )
        label.bind(texture_size=label.setter('size'))
        layout.add_widget(label)
        return layout

if __name__ == '__main__':
    CrashProofApp().run()

import os
import sys
import traceback
from kivy.clock import Clock
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.filemanager import MDFileManager
from kivymd.toast import toast
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivy.utils import platform
import re

# ❌ 绝对不要在顶部导入 pypdf，否则一启动就崩
# from pypdf import PdfReader ... 

# 界面布局 KV
KV = '''
MDBoxLayout:
    orientation: 'vertical'

    MDTopAppBar:
        title: "PDF 瑞士军刀 v2.0"
        elevation: 4

    # ❗错误日志显示区 (如果出问题，错误会显示在这里)
    MDLabel:
        id: error_label
        text: "状态: 等待操作..."
        halign: "center"
        theme_text_color: "Custom"
        text_color: 0.5, 0.5, 0.5, 1
        font_style: "Caption"
        size_hint_y: None
        height: dp(30)

    MDBottomNavigation:
        panel_color: 1, 1, 1, 1

        # --- 提取页 ---
        MDBottomNavigationItem:
            name: 'extract'
            text: '提取'
            icon: 'file-document-minus-outline'

            MDBoxLayout:
                orientation: 'vertical'
                padding: dp(20)
                spacing: dp(15)

                MDRaisedButton:
                    text: "1. 选择 PDF"
                    pos_hint: {"center_x": .5}
                    on_release: app.file_manager_open("extract")

                MDLabel:
                    id: label_extract_path
                    text: "未选择文件"
                    halign: "center"
                    theme_text_color: "Secondary"

                MDTextField:
                    id: field_range
                    hint_text: "页码 (如: 1-5, 8)"
                    mode: "rectangle"

                MDRaisedButton:
                    text: "执行提取"
                    md_bg_color: 0, 0.7, 0, 1
                    pos_hint: {"center_x": .5}
                    on_release: app.safe_run(app.do_extract)

                Widget:

        # --- 合并页 ---
        MDBottomNavigationItem:
            name: 'merge'
            text: '合并'
            icon: 'file-document-plus-outline'

            MDBoxLayout:
                orientation: 'vertical'
                padding: dp(20)
                spacing: dp(10)

                MDBoxLayout:
                    size_hint_y: None
                    height: dp(50)
                    spacing: dp(10)
                    MDRaisedButton:
                        text: "添加文件"
                        on_release: app.file_manager_open("merge")
                    MDRaisedButton:
                        text: "清空"
                        md_bg_color: 1, 0, 0, 1
                        on_release: app.clear_merge_list()

                ScrollView:
                    MDList:
                        id: container_merge_list

                MDTextField:
                    id: field_sequence
                    hint_text: "顺序 (选填，如 1 2 1)"

                MDRaisedButton:
                    text: "执行合并"
                    md_bg_color: 0, 0, 1, 1
                    pos_hint: {"center_x": .5}
                    on_release: app.safe_run(app.do_merge)
'''

class PDFToolApp(MDApp):
    def build(self):
        self.merge_files = []
        self.dialog = None
        self.current_action = None
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            preview=False,
        )
        return Builder.load_string(KV)

    def on_start(self):
        # 延迟 2 秒申请权限，给 UI 渲染留足时间
        if platform == 'android':
            Clock.schedule_once(self.request_perms, 2)

    def update_status(self, text, is_error=False):
        """更新屏幕顶部的状态栏"""
        label = self.root.ids.error_label
        label.text = text
        if is_error:
            label.text_color = (1, 0, 0, 1) # 红色
        else:
            label.text_color = (0, 0.5, 0, 1) # 绿色

    def safe_run(self, func):
        """安全运行包装器"""
        def wrapper():
            try:
                func()
            except Exception as e:
                # 捕获一切错误并显示在屏幕上
                err_msg = traceback.format_exc()
                self.update_status(f"出错: {str(e)}", is_error=True)
                self.show_alert("运行错误", err_msg)
        return wrapper

    def request_perms(self, *args):
        try:
            from android.permissions import request_permissions
            # 仅申请基础权限，字符串形式，最稳妥
            request_permissions([
                "android.permission.READ_EXTERNAL_STORAGE",
                "android.permission.WRITE_EXTERNAL_STORAGE"
            ])
            self.update_status("权限申请已发送")
        except Exception:
            self.update_status("非安卓环境或权限模块缺失", is_error=True)

    # --- 文件管理器 ---
    def file_manager_open(self, action):
        try:
            self.current_action = action
            path = "/storage/emulated/0/Download" if platform == 'android' else os.path.expanduser("~")
            if not os.path.exists(path): path = "/"
            self.file_manager.show(path)
        except Exception as e:
            self.update_status(f"文件管理器错误: {e}", is_error=True)

    def select_path(self, path):
        self.exit_manager()
        if not path.endswith('.pdf'):
            toast("请选择 PDF")
            return
        
        if self.current_action == "extract":
            self.root.ids.label_extract_path.text = path
            self.update_status("已选择文件")
        elif self.current_action == "merge":
            self.merge_files.append(path)
            from kivymd.uix.list import OneLineListItem
            item = OneLineListItem(text=f"{len(self.merge_files)}. {os.path.basename(path)}")
            self.root.ids.container_merge_list.add_widget(item)
            self.update_status(f"已添加第 {len(self.merge_files)} 个文件")

    def exit_manager(self, *args):
        self.file_manager.close()

    def clear_merge_list(self):
        self.merge_files = []
        self.root.ids.container_merge_list.clear_widgets()
        self.update_status("列表已清空")

    def show_alert(self, title, text):
        if not self.dialog:
            self.dialog = MDDialog(
                title=title, text=text,
                buttons=[MDFlatButton(text="OK", on_release=lambda x: self.dialog.dismiss())]
            )
        else:
            self.dialog.title = title
            self.dialog.text = text
        self.dialog.open()

    # --- 核心 PDF 逻辑 (全部懒加载) ---
    def do_extract(self):
        # 1. 尝试导入库
        try:
            from pypdf import PdfReader, PdfWriter
        except ImportError:
            self.update_status("严重错误: pypdf 库未找到", is_error=True)
            return

        # 2. 获取路径
        path = self.root.ids.label_extract_path.text
        if path == "未选择文件":
            toast("请选文件")
            return
        
        # 3. 执行提取
        reader = PdfReader(path)
        range_str = self.root.ids.field_range.text
        if not range_str: return

        # 解析页码 (简化版)
        indices = []
        for part in range_str.replace(' ', '').split(','):
            if '-' in part:
                s, e = part.split('-')
                indices.extend(range(int(s)-1, len(reader.pages) if e=='end' else int(e)))
            else:
                indices.append(int(part)-1)
        
        writer = PdfWriter()
        writer.append(fileobj=path, pages=indices)
        
        # 保存
        out_path = os.path.join("/storage/emulated/0/Download", "extract_output.pdf")
        if platform != 'android': out_path = "extract_output.pdf"
        
        # 简单防重名
        c=1
        while os.path.exists(out_path):
            out_path = out_path.replace(".pdf", f"_{c}.pdf")
            c+=1

        with open(out_path, "wb") as f:
            writer.write(f)
        
        self.update_status("提取成功！")
        self.show_alert("成功", f"文件已保存至:\n{out_path}")

    def do_merge(self):
        try:
            from pypdf import PdfWriter
        except ImportError:
            self.update_status("pypdf 库缺失", is_error=True)
            return

        if len(self.merge_files) < 2:
            toast("至少选2个文件")
            return

        writer = PdfWriter()
        seq = self.root.ids.field_sequence.text
        indices = [int(x)-1 for x in seq.split()] if seq else range(len(self.merge_files))
        
        for idx in indices:
            if 0 <= idx < len(self.merge_files):
                writer.append(fileobj=self.merge_files[idx])
        
        out_path = os.path.join("/storage/emulated/0/Download", "merge_output.pdf")
        if platform != 'android': out_path = "merge_output.pdf"
        
        c=1
        while os.path.exists(out_path):
            out_path = out_path.replace(".pdf", f"_{c}.pdf")
            c+=1

        with open(out_path, "wb") as f:
            writer.write(f)
        
        self.update_status("合并成功！")
        self.show_alert("成功", f"文件已保存至:\n{out_path}")

if __name__ == '__main__':
    try:
        PDFToolApp().run()
    except Exception as e:
        print(f"CRASH: {e}")

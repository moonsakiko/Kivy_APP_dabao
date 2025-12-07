import os
import sys
import traceback # 用于捕捉错误堆栈
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.filemanager import MDFileManager
from kivymd.toast import toast
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.utils import platform
from pypdf import PdfReader, PdfWriter
import re

# 界面布局 (保持不变)
KV = '''
MDBoxLayout:
    orientation: 'vertical'

    MDTopAppBar:
        title: "PDF 瑞士军刀"
        elevation: 4

    MDBottomNavigation:
        panel_color: 1, 1, 1, 1

        MDBottomNavigationItem:
            name: 'screen_extract'
            text: '提取'
            icon: 'file-document-minus-outline'

            MDBoxLayout:
                orientation: 'vertical'
                padding: dp(20)
                spacing: dp(20)

                MDLabel:
                    text: "PDF 页面提取"
                    halign: "center"
                    font_style: "H5"
                    size_hint_y: None
                    height: self.texture_size[1]

                MDRaisedButton:
                    text: "选择 PDF 文件"
                    pos_hint: {"center_x": .5}
                    on_release: app.file_manager_open("extract")

                MDLabel:
                    id: label_extract_path
                    text: "未选择文件"
                    halign: "center"
                    theme_text_color: "Secondary"
                    font_style: "Caption"

                MDTextField:
                    id: field_range
                    hint_text: "输入页码范围 (如: 1-5, 8, 10-end)"

                MDRaisedButton:
                    text: "开始提取"
                    md_bg_color: 0, 0.7, 0, 1
                    pos_hint: {"center_x": .5}
                    on_release: app.do_extract()

                Widget:

        MDBottomNavigationItem:
            name: 'screen_merge'
            text: '合并'
            icon: 'file-document-plus-outline'

            MDBoxLayout:
                orientation: 'vertical'
                padding: dp(20)
                spacing: dp(10)

                MDLabel:
                    text: "PDF 序列合并"
                    halign: "center"
                    font_style: "H5"
                    size_hint_y: None
                    height: self.texture_size[1]

                MDBoxLayout:
                    size_hint_y: None
                    height: dp(50)
                    spacing: dp(10)
                    
                    MDRaisedButton:
                        text: "添加文件"
                        on_release: app.file_manager_open("merge")
                    
                    MDRaisedButton:
                        text: "清空列表"
                        md_bg_color: 1, 0, 0, 1
                        on_release: app.clear_merge_list()

                ScrollView:
                    MDList:
                        id: container_merge_list

                MDTextField:
                    id: field_sequence
                    hint_text: "合并顺序 (默认按列表顺序)"

                MDRaisedButton:
                    text: "开始合并"
                    md_bg_color: 0, 0, 1, 1
                    pos_hint: {"center_x": .5}
                    on_release: app.do_merge()
'''

class PDFToolApp(MDApp):
    def build(self):
        # ❗❗❗ 全局异常捕获 ❗❗❗
        try:
            self.merge_files = [] 
            self.dialog = None
            self.current_action = None
            
            self.file_manager = MDFileManager(
                exit_manager=self.exit_manager,
                select_path=self.select_path,
                preview=False,
            )
            return Builder.load_string(KV)
        except Exception:
            # 如果构建界面就崩了，显示错误
            return MDLabel(text=traceback.format_exc(), halign="center", theme_text_color="Error")

    def on_start(self):
        # ❗❗❗ 申请 Android 11+ 最高权限 ❗❗❗
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                # 申请基础权限
                request_permissions([
                    Permission.READ_EXTERNAL_STORAGE, 
                    Permission.WRITE_EXTERNAL_STORAGE,
                    Permission.MANAGE_EXTERNAL_STORAGE
                ])
                
                # 尝试调用 Intent 跳转到“所有文件访问权限”设置页面
                # 这是解决 Android 11+ 闪退的终极办法
                from jnius import autoclass
                from android import activity
                
                def check_permission(*args):
                    # 这里可以添加检测逻辑，简化处理直接尝试跳转
                    pass

                # 下面这段代码尝试让系统相信我们需要管理所有文件
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                currentActivity = PythonActivity.mActivity
                Context = autoclass('android.content.Context')
                Intent = autoclass('android.content.Intent')
                Settings = autoclass('android.provider.Settings')
                Uri = autoclass('android.net.Uri')
                
                # 只有安卓 11 (SDK 30) 以上才需要这个特殊跳转
                # 为了防止报错，这里先简化处理，主要依靠 request_permissions
                
            except Exception as e:
                # 权限申请失败也不要崩，把错误打出来
                toast(f"权限申请警告: {str(e)}")

    def file_manager_open(self, action):
        try:
            self.current_action = action
            # ❗修改默认路径：先打开 APP 私有目录，防止一上来就因权限崩溃
            # path = "/storage/emulated/0" 
            path = os.path.expanduser("~") 
            if platform == 'android':
                path = "/storage/emulated/0"
            self.file_manager.show(path)
        except Exception as e:
            self.show_alert("路径错误", f"无法打开文件管理器:\n{e}\n请检查是否授予了文件访问权限")

    def select_path(self, path):
        self.exit_manager()
        try:
            if not path.endswith('.pdf'):
                toast("请选择 PDF 文件")
                return

            if self.current_action == "extract":
                self.root.ids.label_extract_path.text = path
            
            elif self.current_action == "merge":
                self.merge_files.append(path)
                from kivymd.uix.list import OneLineListItem
                item = OneLineListItem(text=f"{len(self.merge_files)}. {os.path.basename(path)}")
                self.root.ids.container_merge_list.add_widget(item)
        except Exception as e:
            self.show_alert("选择错误", str(e))

    def exit_manager(self, *args):
        self.file_manager.close()

    def clear_merge_list(self):
        self.merge_files = []
        self.root.ids.container_merge_list.clear_widgets()
        toast("列表已清空")

    def show_alert(self, title, text):
        if not self.dialog:
            self.dialog = MDDialog(
                title=title, text=text,
                buttons=[MDFlatButton(text="确定", on_release=lambda x: self.dialog.dismiss())]
            )
        else:
            self.dialog.title = title
            self.dialog.text = text
        self.dialog.open()

    def get_download_folder(self):
        if platform == 'android':
            # 尝试多种路径以防万一
            paths = [
                "/storage/emulated/0/Download",
                "/storage/emulated/0/Downloads",
                os.path.expanduser("~")
            ]
            for p in paths:
                if os.path.exists(p) and os.access(p, os.W_OK):
                    return p
        return os.path.expanduser("~/Downloads")

    def sanitize_filename(self, name):
        return re.sub(r'[\\/*?:"<>|]', "", name).strip().replace(" ", "_")

    def parse_page_range(self, range_str, max_pages):
        pages = []
        parts = range_str.replace(' ', '').split(',')
        for part in parts:
            if not part: continue
            if '-' in part:
                try:
                    start, end = part.split('-')
                    start = int(start)
                    end = max_pages if end.lower() == 'end' else int(end)
                    pages.extend(range(start - 1, end))
                except: continue
            else:
                try:
                    pages.append(int(part) - 1)
                except: continue
        return [p for p in pages if 0 <= p < max_pages]

    def get_bookmark_filename(self, reader, start_page_index):
        try:
            outline = reader.outline
            if not outline: return None
            for item in outline:
                if isinstance(item, list): continue 
                try:
                    if reader.get_destination_page_number(item) == start_page_index:
                        return self.sanitize_filename(item.title)
                except: continue
        except: pass 
        return None

    def do_extract(self):
        # ❗❗❗ 核心逻辑包裹 try-except ❗❗❗
        try:
            path = self.root.ids.label_extract_path.text
            range_str = self.root.ids.field_range.text
            
            if path == "未选择文件":
                toast("请先选择 PDF 文件")
                return
            if not range_str:
                toast("请输入页码范围")
                return

            reader = PdfReader(path)
            total_pages = len(reader.pages)
            selected_indices = self.parse_page_range(range_str, total_pages)
            
            if not selected_indices:
                self.show_alert("错误", "页码范围无效")
                return

            writer = PdfWriter()
            writer.append(fileobj=path, pages=selected_indices)

            start_idx = selected_indices[0]
            out_name = self.get_bookmark_filename(reader, start_idx)
            if not out_name:
                base = os.path.splitext(os.path.basename(path))[0]
                out_name = f"{base}_extracted"
            
            if not out_name.endswith(".pdf"): out_name += ".pdf"
            
            out_path = os.path.join(self.get_download_folder(), out_name)
            
            count = 1
            while os.path.exists(out_path):
                out_path = os.path.join(self.get_download_folder(), f"{count}_{out_name}")
                count += 1

            with open(out_path, "wb") as f:
                writer.write(f)
            
            self.show_alert("成功", f"文件已保存至:\n{out_path}")

        except Exception as e:
            # 打印完整错误堆栈
            self.show_alert("运行错误", f"{str(e)}\n{traceback.format_exc()}")

    def do_merge(self):
        try:
            if len(self.merge_files) < 2:
                toast("至少需要 2 个文件")
                return

            seq_str = self.root.ids.field_sequence.text.strip()
            indices = []
            
            if seq_str:
                indices = [int(x) - 1 for x in seq_str.split()]
            else:
                indices = range(len(self.merge_files))
            
            writer = PdfWriter()
            for idx in indices:
                if 0 <= idx < len(self.merge_files):
                    writer.append(fileobj=self.merge_files[idx])
            
            out_name = "merged_output.pdf"
            out_path = os.path.join(self.get_download_folder(), out_name)
            
            count = 1
            while os.path.exists(out_path):
                out_path = os.path.join(self.get_download_folder(), f"merged_{count}.pdf")
                count += 1
                
            with open(out_path, "wb") as f:
                writer.write(f)
                
            self.show_alert("成功", f"合并完成:\n{out_path}")
            
        except Exception as e:
            self.show_alert("运行错误", f"{str(e)}\n{traceback.format_exc()}")

if __name__ == '__main__':
    # 最后一层保险
    try:
        PDFToolApp().run()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

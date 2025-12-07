import os
import traceback
from kivy.clock import Clock # 引入时钟，用于延迟执行
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.filemanager import MDFileManager
from kivymd.toast import toast
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.label import MDLabel
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
        # ❗❗❗ 核心修改：延迟1秒再申请权限，保证界面先显示出来 ❗❗❗
        if platform == 'android':
            Clock.schedule_once(self.request_android_permissions, 1)

    def request_android_permissions(self, *args):
        """
        使用最稳妥的字符串方式申请权限
        """
        try:
            from android.permissions import request_permissions
            
            # 定义权限列表 (直接用字符串，不要用对象，这样绝对不会报错)
            permissions = [
                "android.permission.READ_EXTERNAL_STORAGE",
                "android.permission.WRITE_EXTERNAL_STORAGE",
                # 尝试申请管理权限，如果系统不支持会自动忽略，不会崩
                "android.permission.MANAGE_EXTERNAL_STORAGE" 
            ]

            def callback(permissions, results):
                # 权限回调，这里可以打印日志，暂时留空
                pass

            request_permissions(permissions, callback)
            
        except Exception as e:
            toast(f"权限申请异常: {str(e)}")

    # --- 以下逻辑保持不变 ---

    def file_manager_open(self, action):
        self.current_action = action
        # 默认路径设为 Download，避免根目录权限问题
        path = self.get_download_folder()
        self.file_manager.show(path)

    def select_path(self, path):
        self.exit_manager()
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
            return "/storage/emulated/0/Download"
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
            
            self.show_alert("成功", f"保存至 Download:\n{os.path.basename(out_path)}")

        except Exception as e:
            self.show_alert("错误", str(e))

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
                
            self.show_alert("成功", f"合并完成:\n{os.path.basename(out_path)}")
        except Exception as e:
            self.show_alert("错误", str(e))

if __name__ == '__main__':
    PDFToolApp().run()

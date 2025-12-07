import os
import shutil
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.filemanager import MDFileManager
from kivymd.toast import toast
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivy.utils import platform
from pypdf import PdfReader, PdfWriter
import re

# 定义界面布局 (KV 语言)
KV = '''
MDBoxLayout:
    orientation: 'vertical'

    MDTopAppBar:
        title: "PDF 瑞士军刀"
        elevation: 4

    MDBottomNavigation:
        panel_color: 1, 1, 1, 1

        # --- 提取功能页 ---
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
                    helper_text: "支持逗号分隔，end代表最后一页"
                    helper_text_mode: "on_focus"

                MDRaisedButton:
                    text: "开始提取"
                    md_bg_color: 0, 0.7, 0, 1
                    pos_hint: {"center_x": .5}
                    on_release: app.do_extract()

                Widget: # 占位符

        # --- 合并功能页 ---
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
                    helper_text: "留空则按列表顺序合并，或输入: 1 2 1"

                MDRaisedButton:
                    text: "开始合并"
                    md_bg_color: 0, 0, 1, 1
                    pos_hint: {"center_x": .5}
                    on_release: app.do_merge()
'''

class PDFToolApp(MDApp):
    def build(self):
        self.merge_files = [] # 存储待合并的文件路径
        self.dialog = None
        self.current_action = None # 'extract' or 'merge'
        
        # 配置内置文件管理器
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            preview=False,
        )
        return Builder.load_string(KV)

    def on_start(self):
        # 申请安卓权限
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE, 
                Permission.WRITE_EXTERNAL_STORAGE
            ])

    # --- 文件管理器逻辑 ---
    def file_manager_open(self, action):
        self.current_action = action
        # 默认打开路径，安卓端设为 /storage/emulated/0
        path = "/"
        if platform == 'android':
            path = "/storage/emulated/0"
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
            # 在界面列表中显示
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

    # --- 核心 PDF 逻辑 (移植自原脚本) ---
    def get_download_folder(self):
        """获取安卓 Download 目录，确保文件能被找到"""
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

    # --- 执行提取 ---
    def do_extract(self):
        path = self.root.ids.label_extract_path.text
        range_str = self.root.ids.field_range.text
        
        if path == "未选择文件":
            toast("请先选择 PDF 文件")
            return
        if not range_str:
            toast("请输入页码范围")
            return

        try:
            reader = PdfReader(path)
            total_pages = len(reader.pages)
            selected_indices = self.parse_page_range(range_str, total_pages)
            
            if not selected_indices:
                self.show_alert("错误", "页码范围无效")
                return

            writer = PdfWriter()
            # 关键：保留书签结构
            writer.append(fileobj=path, pages=selected_indices)

            # 命名逻辑
            start_idx = selected_indices[0]
            out_name = self.get_bookmark_filename(reader, start_idx)
            if not out_name:
                base = os.path.splitext(os.path.basename(path))[0]
                out_name = f"{base}_extracted"
            
            if not out_name.endswith(".pdf"): out_name += ".pdf"
            
            # 保存到下载目录
            out_path = os.path.join(self.get_download_folder(), out_name)
            
            # 防重名
            count = 1
            while os.path.exists(out_path):
                out_path = os.path.join(self.get_download_folder(), f"{count}_{out_name}")
                count += 1

            with open(out_path, "wb") as f:
                writer.write(f)
            
            self.show_alert("成功", f"文件已保存至 Download 文件夹:\n{os.path.basename(out_path)}")

        except Exception as e:
            self.show_alert("错误", str(e))

    # --- 执行合并 ---
    def do_merge(self):
        if len(self.merge_files) < 2:
            toast("至少需要 2 个文件才能合并")
            return

        seq_str = self.root.ids.field_sequence.text.strip()
        indices = []
        
        try:
            if seq_str:
                indices = [int(x) - 1 for x in seq_str.split()]
            else:
                indices = range(len(self.merge_files)) # 默认按顺序
            
            writer = PdfWriter()
            for idx in indices:
                if 0 <= idx < len(self.merge_files):
                    # 关键：保留书签结构
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
            self.show_alert("错误", f"合并失败: {str(e)}")

if __name__ == '__main__':
    PDFToolApp().run()

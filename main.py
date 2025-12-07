import os
import traceback
# ❌ 不要在这里导入 pypdf，会导致启动闪退！
# from pypdf import PdfReader, PdfWriter 

from kivy.clock import Clock
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.filemanager import MDFileManager
from kivymd.toast import toast
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.label import MDLabel
from kivy.utils import platform
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
        
        # 配置内置文件管理器
        # 注意：不要在 build 里做太复杂的操作
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            preview=False,
        )
        return Builder.load_string(KV)

    def on_start(self):
        # 延迟1秒申请权限，确保界面已经渲染出来
        # 这样即使权限申请有问题，用户也能看到界面，而不是黑屏
        if platform == 'android':
            Clock.schedule_once(self.request_android_permissions, 1)

    def request_android_permissions(self, *args):
        try:
            from android.permissions import request_permissions
            # 使用字符串申请权限，最稳妥
            permissions = [
                "android.permission.READ_EXTERNAL_STORAGE",
                "android.permission.WRITE_EXTERNAL_STORAGE",
            ]
            request_permissions(permissions)
        except Exception as e:
            toast(f"权限加载部分异常: {e}")

    # --- 辅助功能 ---
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

    def get_download_folder(self):
        if platform == 'android':
            return "/storage/emulated/0/Download"
        return os.path.expanduser("~/Downloads")

    def sanitize_filename(self, name):
        return re.sub(r'[\\/*?:"<>|]', "", name).strip().replace(" ", "_")

    # --- 文件管理 ---
    def file_manager_open(self, action):
        try:
            self.current_action = action
            # 默认打开 Download 目录
            path = self.get_download_folder()
            if not os.path.exists(path):
                path = "/" # 如果 Download 不存在，回退到根目录
            self.file_manager.show(path)
        except Exception as e:
            self.show_alert("错误", f"无法打开文件管理器: {e}")

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

    # --- 核心逻辑 (懒加载模式) ---
    
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
        # 简单的书签获取逻辑
        try:
            if not reader.outline: return None
            for item in reader.outline:
                if isinstance(item, list): continue
                if reader.get_destination_page_number(item) == start_page_index:
                    return self.sanitize_filename(item.title)
        except: pass
        return None

    def do_extract(self):
        try:
            # ✅ 关键点：只有点击按钮时，才导入 pypdf
            # 如果这里报错，会直接弹出窗口，而不会导致APP闪退
            from pypdf import PdfReader, PdfWriter 
        except ImportError:
            self.show_alert("错误", "pypdf 库加载失败，请检查打包环境")
            return

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
                self.show_alert("提示", "页码范围无效")
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
            
            # 简单的防重名
            c = 1
            while os.path.exists(out_path):
                out_path = os.path.join(self.get_download_folder(), f"{c}_{out_name}")
                c += 1

            with open(out_path, "wb") as f:
                writer.write(f)
            
            self.show_alert("成功", f"文件已保存至:\n{out_path}")

        except Exception as e:
            self.show_alert("执行错误", f"{str(e)}\n{traceback.format_exc()}")

    def do_merge(self):
        try:
            # ✅ 关键点：懒加载
            from pypdf import PdfWriter 
        except ImportError:
            self.show_alert("错误", "pypdf 库加载失败")
            return

        try:
            if len(self.merge_files) < 2:
                toast("至少需要 2 个文件")
                return
            
            # 简单合并逻辑
            writer = PdfWriter()
            seq_str = self.root.ids.field_sequence.text.strip()
            indices = [int(x)-1 for x in seq_str.split()] if seq_str else range(len(self.merge_files))

            for idx in indices:
                if 0 <= idx < len(self.merge_files):
                    writer.append(fileobj=self.merge_files[idx])

            out_path = os.path.join(self.get_download_folder(), "merged_output.pdf")
            c = 1
            while os.path.exists(out_path):
                out_path = os.path.join(self.get_download_folder(), f"merged_{c}.pdf")
                c += 1
            
            with open(out_path, "wb") as f:
                writer.write(f)
                
            self.show_alert("成功", f"合并完成:\n{out_path}")
        except Exception as e:
            self.show_alert("执行错误", str(e))

if __name__ == '__main__':
    # 全局捕获，防止启动瞬间崩溃
    try:
        PDFToolApp().run()
    except Exception as e:
        # 如果连界面都画不出来，就打印到控制台（Logcat）
        print(f"CRITICAL CRASH: {e}")

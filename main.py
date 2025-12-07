import os
import traceback
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.utils import platform

# 保持懒加载，防止启动崩溃
# from pypdf import ... (不要在这里导入)

class PDFApp(App):
    def build(self):
        self.selected_file = None
        self.merge_list = []
        
        # 主布局
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 1. 状态标签
        self.status_label = Label(text="状态: 就绪 (Kivy 2.2.0)", size_hint_y=0.1, color=(0, 1, 0, 1))
        self.layout.add_widget(self.status_label)

        # 2. 文件路径显示
        self.path_label = Label(text="未选择文件", size_hint_y=0.1)
        self.layout.add_widget(self.path_label)

        # 3. 选择文件按钮
        btn_select = Button(text="选择 PDF 文件", size_hint_y=0.1)
        btn_select.bind(on_release=self.show_file_chooser)
        self.layout.add_widget(btn_select)

        # 4. 页码输入框
        self.input_range = TextInput(hint_text="输入页码 (如 1-5)", size_hint_y=0.1, multiline=False)
        self.layout.add_widget(self.input_range)

        # 5. 提取按钮
        btn_extract = Button(text="执行提取", size_hint_y=0.1, background_color=(0, 0.5, 1, 1))
        btn_extract.bind(on_release=self.do_extract)
        self.layout.add_widget(btn_extract)
        
        # 6. 权限按钮 (手动触发)
        btn_perm = Button(text="申请权限 (如果无法读取请点我)", size_hint_y=0.1)
        btn_perm.bind(on_release=self.request_perms)
        self.layout.add_widget(btn_perm)

        return self.layout

    def log(self, msg, error=False):
        self.status_label.text = msg
        self.status_label.color = (1, 0, 0, 1) if error else (0, 1, 0, 1)

    def request_perms(self, *args):
        if platform == 'android':
            try:
                from android.permissions import request_permissions
                request_permissions([
                    "android.permission.READ_EXTERNAL_STORAGE", 
                    "android.permission.WRITE_EXTERNAL_STORAGE"
                ])
                self.log("权限申请已发送")
            except Exception as e:
                self.log(f"权限错误: {e}", True)

    def show_file_chooser(self, *args):
        # 简单的原生文件选择弹窗
        content = BoxLayout(orientation='vertical')
        
        # 默认路径
        path = "/storage/emulated/0/Download" if platform == 'android' else os.path.expanduser("~")
        if not os.path.exists(path): path = "/"
            
        filechooser = FileChooserListView(path=path, filters=['*.pdf'])
        
        btn_box = BoxLayout(size_hint_y=0.1)
        btn_cancel = Button(text="取消")
        btn_select = Button(text="确定")
        
        btn_box.add_widget(btn_cancel)
        btn_box.add_widget(btn_select)
        content.add_widget(filechooser)
        content.add_widget(btn_box)
        
        popup = Popup(title="选择文件", content=content, size_hint=(0.9, 0.9))
        
        def select(instance):
            if filechooser.selection:
                self.selected_file = filechooser.selection[0]
                self.path_label.text = os.path.basename(self.selected_file)
                self.log("已选择: " + self.path_label.text)
            popup.dismiss()
            
        btn_cancel.bind(on_release=popup.dismiss)
        btn_select.bind(on_release=select)
        popup.open()

    def do_extract(self, *args):
        try:
            from pypdf import PdfReader, PdfWriter
        except ImportError:
            self.log("错误: pypdf 库未安装", True)
            return

        if not self.selected_file:
            self.log("请先选择文件!", True)
            return

        range_str = self.input_range.text.strip()
        if not range_str:
            self.log("请输入页码!", True)
            return

        try:
            reader = PdfReader(self.selected_file)
            writer = PdfWriter()
            
            indices = []
            for part in range_str.replace(' ', '').split(','):
                if '-' in part:
                    s, e = part.split('-')
                    indices.extend(range(int(s)-1, len(reader.pages) if e=='end' else int(e)))
                else:
                    indices.append(int(part)-1)

            writer.append(fileobj=self.selected_file, pages=indices)
            
            save_dir = "/storage/emulated/0/Download" if platform == 'android' else "."
            out_name = f"extracted_{os.path.basename(self.selected_file)}"
            out_path = os.path.join(save_dir, out_name)
            
            with open(out_path, "wb") as f:
                writer.write(f)
            
            self.log(f"成功保存至 Download 目录")
            
        except Exception as e:
            self.log(f"失败: {str(e)}", True)

if __name__ == '__main__':
    try:
        PDFApp().run()
    except Exception as e:
        print(f"CRASH: {e}")

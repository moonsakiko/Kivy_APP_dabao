import os
import traceback
from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.utils import platform
from kivy.graphics import Color, Rectangle

# --- 1. 字体注入 (核心修复) ---
# 只要目录下有 font.ttf，所有文字都会自动变成中文
try:
    # 替换 Kivy 默认字体
    LabelBase.register(name='Roboto', fn_regular='font.ttf') 
    LabelBase.register(name='Roboto', fn_regular='font.ttf')
except:
    pass

# --- 2. 自定义美化组件 (为了不丑) ---
class ColoredBox(BoxLayout):
    """带背景色的布局"""
    def __init__(self, color=(1, 1, 1, 1), **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*color)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)
    
    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

class FlatButton(Button):
    """扁平化按钮 (去除原生Kivy的灰色浮雕感)"""
    def __init__(self, bg_color=(0.2, 0.6, 1, 1), **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''  # 去除默认背景图
        self.background_color = bg_color
        self.font_name = 'font.ttf' # 强制指定字体
        self.font_size = '18sp'

# --- 3. 主程序逻辑 ---
class PDFApp(App):
    def build(self):
        self.selected_file = None
        
        # 整体背景设为浅灰，显得高级
        root = ColoredBox(orientation='vertical', color=(0.95, 0.95, 0.95, 1))
        
        # --- 顶部标题栏 ---
        header = ColoredBox(orientation='horizontal', size_hint_y=None, height='60dp', color=(0.1, 0.1, 0.1, 1))
        title = Label(text="PDF 瑞士军刀", font_size='22sp', color=(1,1,1,1), font_name='font.ttf', bold=True)
        header.add_widget(title)
        root.add_widget(header)

        # --- 内容区域 ---
        content = BoxLayout(orientation='vertical', padding='20dp', spacing='20dp')
        
        # 状态显示
        self.status_label = Label(text="准备就绪", color=(0.2, 0.2, 0.2, 1), size_hint_y=None, height='40dp', font_name='font.ttf')
        content.add_widget(self.status_label)

        # 文件路径显示框 (带边框效果)
        self.path_input = TextInput(
            text="尚未选择文件", 
            readonly=True, 
            size_hint_y=None, 
            height='50dp',
            background_color=(1, 1, 1, 1),
            foreground_color=(0.3, 0.3, 0.3, 1),
            font_name='font.ttf'
        )
        content.add_widget(self.path_input)

        # 按钮：选择文件
        btn_select = FlatButton(text="📂 选择 PDF 文件", bg_color=(0.2, 0.6, 0.8, 1), size_hint_y=None, height='60dp')
        btn_select.bind(on_release=self.show_file_chooser)
        content.add_widget(btn_select)

        # 输入框：页码
        self.range_input = TextInput(
            hint_text="输入提取页码 (例如: 1-5, 8)", 
            size_hint_y=None, 
            height='50dp',
            multiline=False,
            font_name='font.ttf'
        )
        content.add_widget(self.range_input)

        # 按钮：执行
        btn_run = FlatButton(text="🚀 开始提取", bg_color=(0.1, 0.7, 0.3, 1), size_hint_y=None, height='60dp')
        btn_run.bind(on_release=self.do_extract)
        content.add_widget(btn_run)
        
        # 占位符，把内容顶上去
        content.add_widget(Label())
        
        root.add_widget(content)
        return root

    def on_start(self):
        # 延迟申请权限
        if platform == 'android':
            Clock.schedule_once(self.request_perms, 1)

    def log(self, msg, is_error=False):
        self.status_label.text = msg
        self.status_label.color = (1, 0, 0, 1) if is_error else (0.1, 0.6, 0.1, 1)

    def request_perms(self, *args):
        try:
            from android.permissions import request_permissions
            request_permissions(["android.permission.READ_EXTERNAL_STORAGE", "android.permission.WRITE_EXTERNAL_STORAGE"])
        except:
            pass

    # --- 文件选择弹窗 (修复中文显示) ---
    def show_file_chooser(self, *args):
        content = BoxLayout(orientation='vertical')
        
        # 路径处理
        start_path = "/storage/emulated/0/Download" if platform == 'android' else "."
        if not os.path.exists(start_path): start_path = "/"

        # ❗关键：FileChooserListView 也要指定字体，否则文件名是方框
        # 但原生控件很难改字体，我们主要依靠全局 LabelBase 替换生效
        filechooser = FileChooserListView(path=start_path, filters=['*.pdf'])
        
        btn_layout = BoxLayout(size_hint_y=None, height='50dp')
        btn_cancel = Button(text="取消", font_name='font.ttf')
        btn_ok = Button(text="确定", font_name='font.ttf')
        
        btn_layout.add_widget(btn_cancel)
        btn_layout.add_widget(btn_ok)
        
        content.add_widget(filechooser)
        content.add_widget(btn_layout)
        
        popup = Popup(title="双击目录进入，单击文件选择", content=content, size_hint=(0.95, 0.95), title_font='font.ttf')
        
        def select(instance):
            if filechooser.selection:
                self.selected_file = filechooser.selection[0]
                self.path_input.text = os.path.basename(self.selected_file)
                self.log("已选中: " + self.path_input.text)
                popup.dismiss()
            else:
                self.log("未选择文件", True)

        btn_cancel.bind(on_release=popup.dismiss)
        btn_ok.bind(on_release=select)
        popup.open()

    # --- 核心逻辑 ---
    def do_extract(self, *args):
        try:
            # 懒加载
            from pypdf import PdfReader, PdfWriter
        except ImportError:
            self.log("缺少 pypdf 库", True)
            return

        if not self.selected_file:
            self.log("请先选择文件", True)
            return
        
        range_str = self.range_input.text
        if not range_str:
            self.log("请输入页码", True)
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
            
            out_path = os.path.join(os.path.dirname(self.selected_file), f"extracted_{os.path.basename(self.selected_file)}")
            
            with open(out_path, "wb") as f:
                writer.write(f)
            
            self.log("成功！保存至原目录")
            self.path_input.text = f"保存成功: {os.path.basename(out_path)}"
            
        except Exception as e:
            self.log(f"错误: {str(e)}", True)

if __name__ == '__main__':
    try:
        PDFApp().run()
    except Exception as e:
        print(e)

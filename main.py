import os
import traceback
from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button, ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.utils import platform
from kivy.graphics import Color, RoundedRectangle, Rectangle

# --- 1. 字体注入 (核心修复) ---
try:
    LabelBase.register(name='Roboto', fn_regular='font.ttf')
    LabelBase.register(name='Roboto-Bold', fn_regular='font.ttf')
except:
    pass

# --- 2. 手写现代化 UI 组件 (这就是"高级"的来源) ---

class ModernCard(BoxLayout):
    """圆角卡片背景"""
    def __init__(self, bg_color=(1, 1, 1, 1), radius=[15,], **kwargs):
        super().__init__(**kwargs)
        self.padding = '15dp'
        with self.canvas.before:
            Color(*bg_color)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=radius)
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

class ModernButton(ButtonBehavior, FloatLayout):
    """手写圆角按钮 (带按下动画)"""
    def __init__(self, text="", bg_color=(0.2, 0.6, 1, 1), **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = '50dp'
        self.bg_color = bg_color
        self.text = text
        
        with self.canvas.before:
            self.color_instruction = Color(*bg_color)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[10,])
        
        self.label = Label(text=text, pos_hint={'center_x': .5, 'center_y': .5}, font_name='font.ttf', bold=True)
        self.add_widget(self.label)
        self.bind(size=self._update, pos=self._update)

    def _update(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def on_press(self):
        # 按下变暗
        self.color_instruction.rgba = [c * 0.8 for c in self.bg_color]

    def on_release(self):
        # 松开恢复
        self.color_instruction.rgba = self.bg_color

# --- 3. 主程序 ---
class PDFApp(App):
    def build(self):
        self.selected_file = None
        
        # 根布局：浅灰色背景
        root = FloatLayout()
        with root.canvas.before:
            Color(0.95, 0.95, 0.97, 1) # 现代化灰背景
            Rectangle(size=(2000, 2000), pos=(0,0)) # 填充背景
            
        # 主容器
        layout = BoxLayout(orientation='vertical', padding='20dp', spacing='15dp')
        
        # 顶部标题
        title = Label(
            text="PDF 大师", 
            font_size='26sp', 
            color=(0.2, 0.2, 0.2, 1), 
            size_hint_y=None, 
            height='60dp', 
            font_name='font.ttf', 
            bold=True
        )
        layout.add_widget(title)

        # 卡片 1：文件选择
        card1 = ModernCard(orientation='vertical', size_hint_y=None, height='140dp')
        
        self.status_label = Label(text="请选择文件", color=(0.5, 0.5, 0.5, 1), font_name='font.ttf')
        card1.add_widget(self.status_label)
        
        self.path_display = TextInput(
            text="", readonly=True, background_color=(0,0,0,0), 
            foreground_color=(0.3, 0.3, 0.3, 1), font_name='font.ttf', 
            multiline=False, hint_text="文件路径将显示在这里"
        )
        card1.add_widget(self.path_display)
        
        btn_select = ModernButton(text="📂 点击选择 PDF", bg_color=(0.2, 0.6, 0.9, 1))
        btn_select.bind(on_release=self.show_file_chooser)
        card1.add_widget(btn_select)
        
        layout.add_widget(card1)

        # 卡片 2：操作区
        card2 = ModernCard(orientation='vertical', size_hint_y=None, height='140dp')
        
        input_label = Label(text="提取范围 (例如 1-5, 8)", color=(0.5,0.5,0.5,1), size_hint_y=None, height='30dp', font_name='font.ttf')
        card2.add_widget(input_label)
        
        self.range_input = TextInput(
            multiline=False, size_hint_y=None, height='40dp',
            font_name='font.ttf', hint_text="输入页码..."
        )
        card2.add_widget(self.range_input)
        
        # 垫片
        card2.add_widget(Label(size_hint_y=None, height='10dp'))
        
        btn_run = ModernButton(text="🚀 开始处理", bg_color=(0.1, 0.7, 0.4, 1))
        btn_run.bind(on_release=self.do_extract)
        card2.add_widget(btn_run)
        
        layout.add_widget(card2)
        
        # 底部占位
        layout.add_widget(Label())
        
        root.add_widget(layout)
        return root

    def on_start(self):
        if platform == 'android':
            Clock.schedule_once(self.request_perms, 1)

    def log(self, msg, is_error=False):
        self.status_label.text = msg
        self.status_label.color = (0.9, 0.2, 0.2, 1) if is_error else (0.2, 0.6, 0.2, 1)

    def request_perms(self, *args):
        try:
            from android.permissions import request_permissions
            request_permissions(["android.permission.READ_EXTERNAL_STORAGE", "android.permission.WRITE_EXTERNAL_STORAGE"])
        except:
            pass

    # --- 文件选择 ---
    def show_file_chooser(self, *args):
        content = BoxLayout(orientation='vertical')
        path = "/storage/emulated/0/Download" if platform == 'android' else "."
        if not os.path.exists(path): path = "/"

        filechooser = FileChooserListView(path=path, filters=['*.pdf'])
        
        btn_box = BoxLayout(size_hint_y=None, height='50dp', spacing='10dp')
        btn_cancel = Button(text="取消", font_name='font.ttf')
        btn_ok = Button(text="选定", font_name='font.ttf', background_color=(0.2, 0.6, 1, 1))
        
        btn_box.add_widget(btn_cancel)
        btn_box.add_widget(btn_ok)
        
        content.add_widget(filechooser)
        content.add_widget(btn_box)
        
        popup = Popup(title="选择 PDF 文件", content=content, size_hint=(0.9, 0.9), title_font='font.ttf')
        
        def select(instance):
            if filechooser.selection:
                self.selected_file = filechooser.selection[0]
                self.path_display.text = os.path.basename(self.selected_file)
                self.log("文件已就绪")
                popup.dismiss()
            else:
                self.log("未选择", True)

        btn_cancel.bind(on_release=popup.dismiss)
        btn_ok.bind(on_release=select)
        popup.open()

    # --- 处理逻辑 (Lazy Import) ---
    def do_extract(self, *args):
        try:
            from pypdf import PdfReader, PdfWriter
        except ImportError:
            self.log("缺少依赖库", True)
            return

        if not self.selected_file:
            self.log("请先选择文件！", True)
            return

        range_str = self.range_input.text
        if not range_str:
            self.log("请输入页码范围", True)
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
            
            # 保存逻辑
            save_dir = "/storage/emulated/0/Download" if platform == 'android' else "."
            out_name = f"提取_{os.path.basename(self.selected_file)}"
            out_path = os.path.join(save_dir, out_name)
            
            with open(out_path, "wb") as f:
                writer.write(f)
            
            self.log("✅ 处理成功！")
            self.show_success_popup(out_path)
            
        except Exception as e:
            self.log(f"出错: {str(e)}", True)

    def show_success_popup(self, path):
        content = BoxLayout(orientation='vertical', padding='10dp')
        content.add_widget(Label(text=f"文件已保存至:\n{path}", font_name='font.ttf', halign='center'))
        btn = Button(text="好的", size_hint_y=None, height='50dp', font_name='font.ttf')
        content.add_widget(btn)
        popup = Popup(title="成功", content=content, size_hint=(0.8, 0.4), title_font='font.ttf')
        btn.bind(on_release=popup.dismiss)
        popup.open()

if __name__ == '__main__':
    try:
        PDFApp().run()
    except Exception as e:
        print(e)

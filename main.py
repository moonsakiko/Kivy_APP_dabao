import os
import traceback
from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.core.text import LabelBase
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button, ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.utils import platform
from kivy.graphics import Color, RoundedRectangle, Rectangle
from plyer import filechooser # ❗引入系统文件选择器

# --- 1. 字体注入 ---
try:
    LabelBase.register(name='Roboto', fn_regular='font.ttf')
    LabelBase.register(name='Roboto-Bold', fn_regular='font.ttf')
except:
    pass

# --- 2. 现代化 UI 组件 ---

class Card(BoxLayout):
    """白色圆角卡片"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.padding = '15dp'
        with self.canvas.before:
            Color(1, 1, 1, 1) # 纯白背景
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[12,])
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

class ColorButton(ButtonBehavior, FloatLayout):
    """彩色圆角按钮"""
    def __init__(self, text="", bg_color=(0.2, 0.6, 1, 1), **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = '55dp'
        self.bg_color = bg_color
        
        with self.canvas.before:
            self.color_node = Color(*bg_color)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[8,])
        
        self.label = Label(text=text, pos_hint={'center_x': .5, 'center_y': .5}, 
                           font_name='font.ttf', bold=True, color=(1,1,1,1))
        self.add_widget(self.label)
        self.bind(size=self._update, pos=self._update)

    def _update(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def on_press(self):
        self.color_node.rgba = [c*0.8 for c in self.bg_color]
    def on_release(self):
        self.color_node.rgba = self.bg_color

# --- 3. 主程序 ---
class PDFApp(App):
    def build(self):
        self.selected_file = None
        
        # 根布局：浅灰背景 (护眼)
        root = FloatLayout()
        with root.canvas.before:
            Color(0.94, 0.94, 0.96, 1)
            Rectangle(size=(3000, 3000), pos=(0,0))

        # 主容器
        layout = BoxLayout(orientation='vertical', padding='20dp', spacing='20dp')
        
        # --- 标题栏 ---
        title = Label(
            text="PDF 提取工具", 
            font_size='24sp', 
            color=(0.2, 0.2, 0.2, 1), 
            size_hint_y=None, 
            height='50dp', 
            font_name='font.ttf', 
            bold=True
        )
        layout.add_widget(title)

        # --- 卡片 1：文件选择区 ---
        card1 = Card(orientation='vertical', size_hint_y=None, height='160dp', spacing='10dp')
        
        self.status_label = Label(text="请选择一个 PDF 文件", color=(0.5, 0.5, 0.5, 1), font_name='font.ttf')
        card1.add_widget(self.status_label)
        
        # 只读输入框显示路径
        self.path_display = TextInput(
            text="", readonly=True, background_color=(0.95, 0.95, 0.95, 1), 
            foreground_color=(0.3, 0.3, 0.3, 1), font_name='font.ttf', 
            multiline=False, hint_text="路径将显示在这里...", size_hint_y=None, height='40dp'
        )
        card1.add_widget(self.path_display)
        
        # 蓝色按钮：调用系统选择器
        btn_select = ColorButton(text="点击调用系统文件选择", bg_color=(0.2, 0.6, 0.9, 1))
        btn_select.bind(on_release=self.call_system_picker)
        card1.add_widget(btn_select)
        
        layout.add_widget(card1)

        # --- 卡片 2：操作区 ---
        card2 = Card(orientation='vertical', size_hint_y=None, height='180dp', spacing='10dp')
        
        lbl_hint = Label(text="请输入提取范围 (例如 1-5, 8)", color=(0.4,0.4,0.4,1), size_hint_y=None, height='30dp', font_name='font.ttf')
        card2.add_widget(lbl_hint)
        
        self.range_input = TextInput(
            multiline=False, size_hint_y=None, height='45dp',
            font_name='font.ttf', hint_text="在此输入页码..."
        )
        card2.add_widget(self.range_input)
        
        # 绿色按钮：开始处理
        btn_run = ColorButton(text="开始提取页面", bg_color=(0.2, 0.7, 0.4, 1))
        btn_run.bind(on_release=self.do_extract)
        card2.add_widget(btn_run)

        # 进度条 (默认隐藏)
        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height='10dp', opacity=0)
        card2.add_widget(self.progress)
        
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

    # --- 核心：调用系统文件选择器 ---
    def call_system_picker(self, *args):
        try:
            # 调用安卓原生选择器
            filechooser.open_file(on_selection=self.handle_selection, filters=[("PDF Files", "*.pdf")])
        except Exception as e:
            self.log(f"系统选择器调用失败: {e}", True)

    # 处理选择结果 (注意：Plyer 是异步的，需要用 @mainthread 回到主线程更新 UI)
    @mainthread
    def handle_selection(self, selection):
        if selection:
            self.selected_file = selection[0]
            # 简单的路径美化，太长就截断
            display_name = os.path.basename(self.selected_file)
            self.path_display.text = display_name
            self.log("✅ 文件已加载")
        else:
            self.log("未选择文件")

    # --- 处理逻辑 ---
    def do_extract(self, *args):
        if not self.selected_file:
            self.log("❌ 请先点击蓝色按钮选择文件", True)
            return

        range_str = self.range_input.text
        if not range_str:
            self.log("❌ 请输入页码", True)
            return

        # 显示进度条
        self.progress.opacity = 1
        self.progress.value = 10
        
        # 延迟执行，让UI有机会刷新进度条
        Clock.schedule_once(lambda dt: self._process_pdf(range_str), 0.1)

    def _process_pdf(self, range_str):
        try:
            from pypdf import PdfReader, PdfWriter
            self.progress.value = 30
            
            reader = PdfReader(self.selected_file)
            writer = PdfWriter()
            
            indices = []
            for part in range_str.replace(' ', '').split(','):
                if '-' in part:
                    s, e = part.split('-')
                    indices.extend(range(int(s)-1, len(reader.pages) if e=='end' else int(e)))
                else:
                    indices.append(int(part)-1)

            self.progress.value = 60
            writer.append(fileobj=self.selected_file, pages=indices)
            
            save_dir = "/storage/emulated/0/Download" if platform == 'android' else "."
            out_name = f"提取_{os.path.basename(self.selected_file)}"
            out_path = os.path.join(save_dir, out_name)
            
            self.progress.value = 80
            with open(out_path, "wb") as f:
                writer.write(f)
            
            self.progress.value = 100
            self.log("✅ 处理完成！")
            self.show_success_popup(out_path)
            
        except Exception as e:
            self.progress.opacity = 0
            self.log(f"出错: {str(e)}", True)

    def show_success_popup(self, path):
        content = BoxLayout(orientation='vertical', padding='10dp', spacing='10dp')
        
        content.add_widget(Label(text="🎉 成功！", font_size='20sp', font_name='font.ttf', bold=True, size_hint_y=None, height='40dp'))
        content.add_widget(Label(text=f"文件已保存至 Download 文件夹:\n{os.path.basename(path)}", font_name='font.ttf', halign='center'))
        
        btn = Button(text="好的", size_hint_y=None, height='50dp', font_name='font.ttf', background_normal='', background_color=(0.2, 0.6, 1, 1))
        content.add_widget(btn)
        
        popup = Popup(title="", separator_height=0, content=content, size_hint=(0.8, 0.5), title_font='font.ttf')
        btn.bind(on_release=popup.dismiss)
        popup.open()
        
        # 1秒后隐藏进度条
        Clock.schedule_once(lambda dt: setattr(self.progress, 'opacity', 0), 1)

if __name__ == '__main__':
    try:
        PDFApp().run()
    except Exception as e:
        print(e)

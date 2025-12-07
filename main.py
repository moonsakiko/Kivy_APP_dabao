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
from kivy.properties import ListProperty, StringProperty

# --- 1. 字体注入 ---
try:
    LabelBase.register(name='Roboto', fn_regular='font.ttf')
    LabelBase.register(name='Roboto-Bold', fn_regular='font.ttf')
except:
    pass

# --- 2. 主题配置 (皮肤引擎) ---
THEMES = {
    "light": {
        "bg": (0.96, 0.96, 0.98, 1),           # 背景灰白
        "card": (1, 1, 1, 1),                  # 卡片纯白
        "text": (0.2, 0.2, 0.2, 1),            # 文字深灰
        "primary": (0.2, 0.6, 1, 1),           # 主色蓝
        "btn_text": (1, 1, 1, 1)               # 按钮文字白
    },
    "dark": {
        "bg": (0.1, 0.1, 0.12, 1),             # 背景深黑
        "card": (0.18, 0.18, 0.2, 1),          # 卡片浅黑
        "text": (0.9, 0.9, 0.9, 1),            # 文字灰白
        "primary": (0.3, 0.7, 0.5, 1),         # 主色绿
        "btn_text": (1, 1, 1, 1)
    },
    "warm": {
        "bg": (0.98, 0.95, 0.9, 1),            # 背景米黄
        "card": (1, 0.98, 0.95, 1),            # 卡片淡黄
        "text": (0.3, 0.2, 0.1, 1),            # 文字暖棕
        "primary": (1, 0.6, 0.4, 1),           # 主色橙
        "btn_text": (1, 1, 1, 1)
    }
}

# --- 3. 现代化 UI 组件 ---

class ThemeManager:
    """管理当前颜色的单例"""
    current_theme = "light"

class ModernCard(BoxLayout):
    """支持换肤的圆角卡片"""
    bg_color = ListProperty(THEMES["light"]["card"])

    def __init__(self, radius=[15,], **kwargs):
        super().__init__(**kwargs)
        self.padding = '15dp'
        with self.canvas.before:
            self.color_node = Color(*self.bg_color)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=radius)
        self.bind(size=self._update_rect, pos=self._update_rect, bg_color=self._update_color)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
    
    def _update_color(self, instance, value):
        self.color_node.rgba = value

class ModernButton(ButtonBehavior, FloatLayout):
    """支持换肤的按钮"""
    bg_color = ListProperty(THEMES["light"]["primary"])
    text_color = ListProperty(THEMES["light"]["btn_text"])

    def __init__(self, text="", **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = '55dp'
        
        with self.canvas.before:
            self.color_node = Color(*self.bg_color)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[10,])
        
        self.label = Label(text=text, pos_hint={'center_x': .5, 'center_y': .5}, 
                           font_name='font.ttf', bold=True, color=self.text_color)
        self.add_widget(self.label)
        
        self.bind(size=self._update, pos=self._update, bg_color=self._update_color)

    def _update(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
    
    def _update_color(self, instance, value):
        self.color_node.rgba = value
        # 按下效果简化，防止闪退
        
    def on_press(self):
        self.color_node.rgba = [c*0.8 for c in self.bg_color]
    def on_release(self):
        self.color_node.rgba = self.bg_color

# --- 4. 主程序 ---
class PDFApp(App):
    # 定义全局颜色属性，方便绑定
    theme_bg = ListProperty(THEMES["light"]["bg"])
    theme_card = ListProperty(THEMES["light"]["card"])
    theme_text = ListProperty(THEMES["light"]["text"])
    theme_primary = ListProperty(THEMES["light"]["primary"])

    def build(self):
        self.selected_file = None
        
        # 根布局
        root = FloatLayout()
        
        # 1. 背景层
        with root.canvas.before:
            self.bg_color_node = Color(*self.theme_bg)
            self.bg_rect = Rectangle(size=(3000, 3000), pos=(0,0))
        # 绑定背景色变化
        self.bind(theme_bg=lambda x,y: setattr(self.bg_color_node, 'rgba', y))

        # 主布局容器
        layout = BoxLayout(orientation='vertical')
        
        # --- 顶部漂亮的标题栏 ---
        header = BoxLayout(size_hint_y=None, height='70dp', padding='15dp', spacing='10dp')
        with header.canvas.before:
            self.header_color = Color(*self.theme_primary)
            Rectangle(size=(3000, 3000), pos=(0,0))
        
        # 绑定标题栏颜色
        self.bind(theme_primary=lambda x,y: setattr(self.header_color, 'rgba', y))

        title_label = Label(text="PDF 大师", font_size='22sp', bold=True, font_name='font.ttf', 
                            halign='left', valign='middle', size_hint_x=0.7)
        title_label.bind(size=title_label.setter('text_size')) # 文本左对齐技巧
        
        # 换肤按钮 (小)
        btn_skin = Button(text="🎨 换肤", size_hint_x=0.3, font_name='font.ttf', 
                          background_normal='', background_color=(1,1,1,0.2))
        btn_skin.bind(on_release=self.toggle_theme)

        header.add_widget(title_label)
        header.add_widget(btn_skin)
        layout.add_widget(header)

        # --- 内容区域 ---
        content = BoxLayout(orientation='vertical', padding='20dp', spacing='20dp')

        # 卡片1：文件显示
        self.card1 = ModernCard(orientation='vertical', size_hint_y=None, height='150dp')
        
        self.status_label = Label(text="尚未选择文件", font_name='font.ttf', color=self.theme_text)
        self.card1.add_widget(self.status_label)
        
        self.path_input = TextInput(readonly=True, multiline=False, height='40dp', size_hint_y=None,
                                    background_color=(0,0,0,0), foreground_color=self.theme_text,
                                    font_name='font.ttf', hint_text="路径...")
        self.card1.add_widget(self.path_input)
        
        self.btn_select = ModernButton(text="📂 点击选择 PDF")
        self.btn_select.bind(on_release=self.show_file_chooser)
        self.card1.add_widget(self.btn_select)
        
        content.add_widget(self.card1)

        # 卡片2：操作
        self.card2 = ModernCard(orientation='vertical', size_hint_y=None, height='150dp')
        
        lbl_hint = Label(text="提取页码 (如 1-5, 8)", font_name='font.ttf', 
                         color=self.theme_text, size_hint_y=None, height='30dp')
        self.card2.add_widget(lbl_hint)
        
        self.range_input = TextInput(multiline=False, height='45dp', size_hint_y=None, font_name='font.ttf')
        self.card2.add_widget(self.range_input)
        
        # 垫片
        self.card2.add_widget(Label(size_hint_y=None, height='10dp'))

        self.btn_run = ModernButton(text="🚀 开始处理")
        self.btn_run.bind(on_release=self.do_extract)
        self.card2.add_widget(self.btn_run)
        
        content.add_widget(self.card2)
        
        # 底部留白
        content.add_widget(Label())
        layout.add_widget(content)
        
        root.add_widget(layout)
        
        # 初始化绑定
        self.update_theme_bindings()
        
        return root

    def on_start(self):
        if platform == 'android':
            Clock.schedule_once(self.request_perms, 1)

    # --- 皮肤切换逻辑 ---
    def toggle_theme(self, *args):
        themes = list(THEMES.keys())
        current = ThemeManager.current_theme
        next_idx = (themes.index(current) + 1) % len(themes)
        ThemeManager.current_theme = themes[next_idx]
        
        # 应用新颜色
        t = THEMES[ThemeManager.current_theme]
        self.theme_bg = t["bg"]
        self.theme_card = t["card"]
        self.theme_text = t["text"]
        self.theme_primary = t["primary"]
        
        self.update_theme_bindings()

    def update_theme_bindings(self):
        # 手动刷新所有组件颜色
        t = THEMES[ThemeManager.current_theme]
        
        self.card1.bg_color = t["card"]
        self.card2.bg_color = t["card"]
        
        self.status_label.color = t["text"]
        self.path_input.foreground_color = t["text"]
        
        self.btn_select.bg_color = t["primary"]
        self.btn_run.bg_color = t["primary"]

    def log(self, msg, is_error=False):
        self.status_label.text = msg
        self.status_label.color = (1, 0, 0, 1) if is_error else self.theme_text

    def request_perms(self, *args):
        try:
            from android.permissions import request_permissions
            request_permissions(["android.permission.READ_EXTERNAL_STORAGE", "android.permission.WRITE_EXTERNAL_STORAGE"])
        except:
            pass

    # --- 文件选择器 (修复 PDF 看不到的问题) ---
    def show_file_chooser(self, *args):
        content = BoxLayout(orientation='vertical')
        
        # 1. 路径修复: 确保进入 Download
        path = "/storage/emulated/0/Download" if platform == 'android' else "."
        if not os.path.exists(path): path = "/"

        # 2. ❗核心修复: 使用 lambda 函数进行忽略大小写的过滤
        # 这样 .pdf, .PDF, .Pdf 都能看到
        filechooser = FileChooserListView(
            path=path, 
            filters=[lambda folder, filename: filename.lower().endswith('.pdf')]
        )
        
        btn_box = BoxLayout(size_hint_y=None, height='50dp', spacing='10dp')
        btn_cancel = Button(text="取消", font_name='font.ttf')
        btn_ok = Button(text="选定", font_name='font.ttf', background_color=self.theme_primary)
        
        btn_box.add_widget(btn_cancel)
        btn_box.add_widget(btn_ok)
        
        content.add_widget(filechooser)
        content.add_widget(btn_box)
        
        popup = Popup(title="请选择文件", content=content, size_hint=(0.95, 0.95), title_font='font.ttf')
        
        def select(instance):
            if filechooser.selection:
                self.selected_file = filechooser.selection[0]
                self.path_input.text = os.path.basename(self.selected_file)
                self.log("已选中文件")
                popup.dismiss()
            else:
                self.log("未选择", True)

        btn_cancel.bind(on_release=popup.dismiss)
        btn_ok.bind(on_release=select)
        popup.open()

    # --- 提取逻辑 ---
    def do_extract(self, *args):
        try:
            from pypdf import PdfReader, PdfWriter
        except ImportError:
            self.log("系统缺少依赖", True)
            return

        if not self.selected_file:
            self.log("请先选择 PDF", True)
            return
        
        if not self.range_input.text:
            self.log("请输入页码", True)
            return

        try:
            reader = PdfReader(self.selected_file)
            writer = PdfWriter()
            indices = []
            for part in self.range_input.text.replace(' ', '').split(','):
                if '-' in part:
                    s, e = part.split('-')
                    indices.extend(range(int(s)-1, len(reader.pages) if e=='end' else int(e)))
                else:
                    indices.append(int(part)-1)

            writer.append(fileobj=self.selected_file, pages=indices)
            
            save_dir = "/storage/emulated/0/Download" if platform == 'android' else "."
            out_name = f"提取_{os.path.basename(self.selected_file)}"
            out_path = os.path.join(save_dir, out_name)
            
            with open(out_path, "wb") as f:
                writer.write(f)
            
            self.log("✅ 成功！")
            self.show_success(out_path)
            
        except Exception as e:
            self.log(f"出错: {e}", True)

    def show_success(self, path):
        content = BoxLayout(orientation='vertical', padding='15dp')
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

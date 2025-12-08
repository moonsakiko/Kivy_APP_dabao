import os
import traceback
from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.utils import platform
from kivy.graphics import Color, RoundedRectangle, Rectangle

# --- 字体加载 ---
# 确保你的仓库里有 font.ttf
try:
    LabelBase.register(name='Roboto', fn_regular='font.ttf')
    LabelBase.register(name='Roboto-Bold', fn_regular='font.ttf')
    has_font = True
except:
    has_font = False

# --- 现代 UI 组件 (手写高颜值) ---

class ModernCard(BoxLayout):
    """带阴影和圆角的卡片"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.padding = '20dp'
        with self.canvas.before:
            # 1. 模拟阴影边框
            Color(0.9, 0.9, 0.92, 1)
            self.border = RoundedRectangle(size=self.size, pos=self.pos, radius=[18,])
            # 2. 纯白背景
            Color(1, 1, 1, 1)
            self.rect = RoundedRectangle(size=(self.width, self.height-2), pos=(self.x, self.y+1), radius=[16,])
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.border.pos = instance.pos
        self.border.size = instance.size
        self.rect.pos = (instance.x + 1, instance.y + 1)
        self.rect.size = (instance.width - 2, instance.height - 2)

class ProButton(ButtonBehavior, FloatLayout):
    """现代化大圆角按钮"""
    def __init__(self, text="", bg_color=(0.2, 0.6, 1, 1), **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = '65dp' # 更适合手指点击的高度
        self.bg_color = bg_color
        
        with self.canvas.before:
            self.color_node = Color(*bg_color)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[12,])
        
        font_args = {'font_name': 'font.ttf'} if has_font else {}
        self.label = Label(text=text, pos_hint={'center_x': .5, 'center_y': .5}, 
                           font_size='18sp', bold=True, color=(1,1,1,1), **font_args)
        self.add_widget(self.label)
        self.bind(size=self._update, pos=self._update)

    def _update(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def on_press(self):
        self.color_node.rgba = [c*0.8 for c in self.bg_color]
    def on_release(self):
        self.color_node.rgba = self.bg_color

# --- 主程序 ---

class PDFApp(App):
    cached_pdf_path = None
    
    def build(self):
        if platform == 'android':
            Clock.schedule_once(self.bind_android, 1)

        # 1. 根布局：高级灰背景
        root = FloatLayout()
        with root.canvas.before:
            Color(0.95, 0.96, 0.98, 1) # 苹果风背景色
            Rectangle(size=(3000, 3000), pos=(0,0))

        # 2. 垂直主容器
        layout = BoxLayout(orientation='vertical', padding='24dp', spacing='20dp')
        
        # 字体配置
        f_title = {'font_name': 'font.ttf'} if has_font else {}
        
        # 3. 标题栏
        header = BoxLayout(orientation='vertical', size_hint_y=None, height='80dp')
        title = Label(text="PDF 大师", font_size='34sp', color=(0.1, 0.1, 0.15, 1), bold=True, 
                      size_hint_x=None, width='300dp', halign='left', **f_title)
        subtitle = Label(text="专业版 v14.0", font_size='14sp', color=(0.5, 0.5, 0.6, 1), 
                         size_hint_x=None, width='300dp', halign='left', **f_title)
        title.bind(texture_size=title.setter('size'))
        header.add_widget(title)
        header.add_widget(subtitle)
        layout.add_widget(header)

        # 4. 操作卡片 (整合选择与输入)
        card = ModernCard(orientation='vertical', size_hint_y=None, height='280dp', spacing='15dp')
        
        # 步骤1
        card.add_widget(Label(text="步骤 1: 导入文件", color=(0.4,0.4,0.4,1), size_hint_y=None, height='20dp', halign='left', text_size=(500, None), **f_title))
        self.path_btn = ProButton(text="📂 点击选择 PDF", bg_color=(0.92, 0.94, 0.96, 1))
        self.path_btn.label.color = (0.2, 0.4, 0.7, 1) # 按钮文字变深色
        self.path_btn.bind(on_release=self.open_picker)
        card.add_widget(self.path_btn)

        # 步骤2
        card.add_widget(Label(text="步骤 2: 提取范围 (如 1-5, 8)", color=(0.4,0.4,0.4,1), size_hint_y=None, height='20dp', halign='left', text_size=(500, None), **f_title))
        self.input_range = TextInput(
            multiline=False, size_hint_y=None, height='55dp', 
            hint_text="在此输入页码...", 
            background_color=(0.98, 0.98, 0.99, 1), cursor_color=(0,0,0,1),
            padding=[15, 15], font_size='16sp', **f_title
        )
        card.add_widget(self.input_range)
        
        layout.add_widget(card)

        # 5. 底部操作区
        self.btn_run = ProButton(text="🚀 开始极速提取", bg_color=(0.1, 0.4, 0.9, 1))
        self.btn_run.bind(on_release=self.do_extract)
        layout.add_widget(self.btn_run)

        # 进度条
        self.prog = ProgressBar(max=100, value=0, size_hint_y=None, height='6dp', opacity=0)
        layout.add_widget(self.prog)

        # 6. 美化的日志区
        scroll = ScrollView(size_hint_y=1) # 占据剩余空间
        self.console = Label(
            text="[系统] 准备就绪...", 
            color=(0.6, 0.6, 0.65, 1), 
            font_size='13sp', 
            size_hint_y=None, 
            halign='left', valign='top', 
            markup=True, **f_title
        )
        self.console.bind(texture_size=self.console.setter('size'))
        self.console.bind(width=lambda instance, value: setattr(instance, 'text_size', (value, None)))
        scroll.add_widget(self.console)
        layout.add_widget(scroll)

        root.add_widget(layout)
        return root

    def log(self, msg, level="INFO"):
        # 颜色代码
        color = "666666"
        if level == "ERROR": color = "ff4444"
        elif level == "SUCCESS": color = "00aa44"
        
        # 使用 >> 代替之前的乱码符号
        new_line = f"[color=#{color}]>> {str(msg)}[/color]\n"
        self.console.text = new_line + self.console.text

    # --- 经过验证的稳健安卓代码 ---
    
    def bind_android(self, dt):
        try:
            from android import activity
            activity.bind(on_activity_result=self.on_result)
        except:
            self.log("非安卓环境", "WARN")

    def open_picker(self, *args):
        if platform == 'android':
            try:
                from jnius import autoclass, cast
                Intent = autoclass('android.content.Intent')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
                
                intent = Intent()
                intent.setAction(Intent.ACTION_GET_CONTENT)
                intent.setType("application/pdf")
                currentActivity.startActivityForResult(intent, 101)
                self.log("正在唤起系统选择器...")
            except Exception as e:
                self.log(f"启动失败: {e}", "ERROR")

    def on_result(self, req, res, intent):
        if req == 101 and res == -1 and intent:
            try:
                uri = intent.getData()
                self.copy_file(uri)
            except Exception as e:
                self.log(f"解析错误: {e}", "ERROR")
        else:
            self.log("未选择文件")

    def copy_file(self, uri):
        try:
            from jnius import autoclass, cast
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            act = cast('android.app.Activity', PythonActivity.mActivity)
            resolver = act.getContentResolver()
            inp = resolver.openInputStream(uri)
            
            cache = act.getCacheDir().getAbsolutePath() + "/temp_process.pdf"
            
            FileOutputStream = autoclass('java.io.FileOutputStream')
            out = FileOutputStream(cache)
            
            buf = bytearray(65536)
            while True:
                n = inp.read(buf)
                if n <= 0: break
                out.write(buf[:n])
            
            inp.close()
            out.close()
            
            self.cached_pdf_path = cache
            self.path_btn.label.text = "✅ PDF 文件已就绪"
            self.path_btn.label.color = (0.1, 0.6, 0.2, 1)
            self.log("文件加载成功！", "SUCCESS")
        except Exception as e:
            self.log(f"IO错误: {e}", "ERROR")

    def do_extract(self, *args):
        if not self.cached_pdf_path:
            self.log("请先完成步骤 1", "ERROR")
            return
        
        raw_range = self.input_range.text
        if not raw_range:
            self.log("请输入页码 (步骤 2)", "ERROR")
            return

        # 进度条动画
        self.prog.opacity = 1
        self.prog.value = 10
        self.log("正在处理...", "INFO")
        Clock.schedule_once(lambda dt: self._process(raw_range), 0.1)

    def _process(self, raw_range):
        try:
            from pypdf import PdfReader, PdfWriter
            self.prog.value = 30
            reader = PdfReader(self.cached_pdf_path)
            writer = PdfWriter()
            
            indices = []
            for part in raw_range.replace(' ', '').split(','):
                if '-' in part:
                    s, e = part.split('-')
                    start = int(s) - 1
                    end = len(reader.pages) if e.lower() == 'end' else int(e)
                    indices.extend(range(start, end))
                else:
                    indices.append(int(part)-1)

            self.prog.value = 60
            writer.append(fileobj=self.cached_pdf_path, pages=indices)
            
            out_path = "/storage/emulated/0/Download/Extract_Pro.pdf"
            # 简单的防重名
            c = 1
            while os.path.exists(out_path):
                out_path = f"/storage/emulated/0/Download/Extract_Pro_{c}.pdf"
                c+=1

            self.prog.value = 80
            with open(out_path, "wb") as f:
                writer.write(f)
            
            self.prog.value = 100
            self.log(f"成功！已保存至 Download", "SUCCESS")
            
            # 3秒后隐藏进度条
            Clock.schedule_once(lambda dt: setattr(self.prog, 'opacity', 0), 3)
            
        except Exception as e:
            self.log(f"失败: {e}", "ERROR")
            self.prog.opacity = 0

if __name__ == '__main__':
    try:
        PDFApp().run()
    except Exception as e:
        print(e)

# main.py
# ❗ 这是一个带有“黑匣子”的调试版本
import traceback
from kivy.app import runTouchApp
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window

# 设置背景色以便看清文字
Window.clearcolor = (0.1, 0.1, 0.1, 1)

try:
    # ================= 你的核心代码开始 =================
    import os
    import datetime
    from kivy.app import App
    from kivy.clock import Clock, mainthread
    from kivy.core.text import LabelBase
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.floatlayout import FloatLayout
    from kivy.uix.button import Button, ButtonBehavior
    from kivy.uix.textinput import TextInput
    from kivy.uix.progressbar import ProgressBar
    from kivy.utils import platform
    from kivy.graphics import Color, RoundedRectangle, Rectangle

    # 尝试加载字体，如果失败不报错，而是用默认字体
    try:
        LabelBase.register(name='Roboto', fn_regular='font.ttf')
        LabelBase.register(name='Roboto-Bold', fn_regular='font.ttf')
        has_font = True
    except:
        has_font = False

    # JNI 初始化放到类内部，防止启动崩溃

    # --- UI 组件 ---
    class Card(BoxLayout):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.padding = '15dp'
            with self.canvas.before:
                Color(0.9, 0.9, 0.92, 1)
                self.border = RoundedRectangle(size=self.size, pos=self.pos, radius=[16,])
                Color(1, 1, 1, 1)
                self.rect = RoundedRectangle(size=(self.width, self.height-2), pos=(self.x, self.y+1), radius=[15,])   
            self.bind(size=self._update_rect, pos=self._update_rect)

        def _update_rect(self, instance, value):
            self.border.pos = instance.pos
            self.border.size = instance.size
            self.rect.pos = (instance.x + 1, instance.y + 1)
            self.rect.size = (instance.width - 2, instance.height - 2)

    class ActionButton(ButtonBehavior, FloatLayout):
        def __init__(self, text="", bg_color=(0.2, 0.6, 1, 1), text_color=(1,1,1,1), **kwargs):
            super().__init__(**kwargs)
            self.size_hint_y = None
            self.height = '60dp'
            self.bg_color = bg_color
            with self.canvas.before:
                self.color_node = Color(*bg_color)
                self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[12,])
            
            font_args = {'font_name': 'font.ttf'} if has_font else {}
            self.label = Label(text=text, pos_hint={'center_x': .5, 'center_y': .5}, 
                               font_size='18sp', bold=True, color=text_color, **font_args)
            self.add_widget(self.label)
            self.bind(size=self._update, pos=self._update)

        def _update(self, instance, value):
            self.rect.pos = instance.pos
            self.rect.size = instance.size

        def on_press(self):
            self.color_node.rgba = [c*0.85 for c in self.bg_color]
        def on_release(self):
            self.color_node.rgba = self.bg_color

    # --- 主程序 ---
    class PDFApp(App):
        cached_pdf_path = None 
        
        def build(self):
            # 延迟绑定 JNI，防止启动卡死
            if platform == 'android':
                Clock.schedule_once(self.bind_android, 1)

            root = FloatLayout()
            with root.canvas.before:
                Color(0.96, 0.96, 0.98, 1)
                Rectangle(size=(3000, 3000), pos=(0,0))

            layout = BoxLayout(orientation='vertical', padding='20dp', spacing='15dp')
            
            # 字体保护
            f_args = {'font_name': 'font.ttf'} if has_font else {}

            # 标题
            title = Label(text="PDF 工具箱", font_size='28sp', color=(0.1,0.1,0.1,1), bold=True, size_hint_y=None, height='60dp', **f_args)
            layout.add_widget(title)

            # 警告信息 (如果字体没加载)
            if not has_font:
                layout.add_widget(Label(text="警告: font.ttf 未找到，使用默认字体", color=(1,0,0,1), size_hint_y=None, height='20dp'))

            # 卡片
            card = Card(orientation='vertical', size_hint_y=None, height='220dp', spacing='10dp')
            self.path_btn = ActionButton(text="点击选择 PDF", bg_color=(0.9, 0.95, 1, 1), text_color=(0.2, 0.4, 0.8, 1))
            self.path_btn.bind(on_release=self.open_picker)
            card.add_widget(self.path_btn)
            
            self.input = TextInput(multiline=False, size_hint_y=None, height='50dp', hint_text="页码 (如 1-5)", **f_args)
            card.add_widget(self.input)
            layout.add_widget(card)

            # 按钮
            btn = ActionButton(text="执行提取", bg_color=(0.1, 0.7, 0.4, 1))
            btn.bind(on_release=self.do_extract)
            layout.add_widget(btn)

            # 进度与日志
            self.prog = ProgressBar(max=100, value=0, size_hint_y=None, height='4dp', opacity=0)
            layout.add_widget(self.prog)

            self.console = Label(text="系统就绪...", color=(0.5,0.5,0.5,1), size_hint_y=None, height='300dp', text_size=(Window.width-40, None), halign='left', valign='top', **f_args)
            layout.add_widget(self.console)

            return root

        def log(self, msg):
            print(msg)
            self.console.text = f"• {str(msg)}\n" + self.console.text

        # --- 安卓逻辑 ---
        def bind_android(self, dt):
            try:
                from android import activity
                activity.bind(on_activity_result=self.on_result)
            except:
                self.log("非安卓环境")

        def open_picker(self, *args):
            if platform == 'android':
                try:
                    from jnius import autoclass
                    Intent = autoclass('android.content.Intent')
                    intent = Intent()
                    intent.setAction(Intent.ACTION_GET_CONTENT)
                    intent.setType("application/pdf")
                    # 纯原生调用
                    from jnius import cast
                    PythonActivity = autoclass('org.kivy.android.PythonActivity')
                    act = cast('android.app.Activity', PythonActivity.mActivity)
                    act.startActivityForResult(intent, 101)
                except Exception as e:
                    self.log(f"启动失败: {e}")

        def on_result(self, req, res, intent):
            if req == 101 and res == -1 and intent:
                try:
                    uri = intent.getData()
                    self.copy_file(uri)
                except Exception as e:
                    self.log(f"文件解析错: {e}")

        def copy_file(self, uri):
            try:
                from jnius import autoclass, cast
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                act = cast('android.app.Activity', PythonActivity.mActivity)
                resolver = act.getContentResolver()
                inp = resolver.openInputStream(uri)
                
                cache = act.getCacheDir().getAbsolutePath() + "/temp.pdf"
                
                # Java IO 写入
                FileOutputStream = autoclass('java.io.FileOutputStream')
                out = FileOutputStream(cache)
                
                # 极简 Buffer (64k)
                buf = bytearray(65536)
                while True:
                    n = inp.read(buf)
                    if n <= 0: break
                    out.write(buf[:n])
                
                inp.close()
                out.close()
                
                self.cached_pdf_path = cache
                self.path_btn.label.text = "✅ 文件已加载"
                self.log("文件加载成功")
            except Exception as e:
                self.log(f"IO错误: {e}")

        def do_extract(self, *args):
            if not self.cached_pdf_path: return self.log("未选文件")
            try:
                from pypdf import PdfReader, PdfWriter
                reader = PdfReader(self.cached_pdf_path)
                writer = PdfWriter()
                # 简单解析
                s_str = self.input.text
                # ... (简化的解析逻辑，防止出错)
                writer.append(fileobj=self.cached_pdf_path, pages=[0]) # 测试用：只提第一页
                
                out = "/storage/emulated/0/Download/result.pdf"
                with open(out, "wb") as f:
                    writer.write(f)
                self.log(f"成功: {out}")
            except Exception as e:
                self.log(f"提取失败: {e}")

    # 启动应用
    PDFApp().run()

except Exception as e:
    # 🚨🚨🚨 终极防线 🚨🚨🚨
    # 如果上面任何代码报错（包括库缺失、语法错误、环境问题）
    # 这里会捕捉到，并把错误直接显示在手机屏幕上！
    error_msg = traceback.format_exc()
    
    # 创建一个极简的报错界面
    layout = ScrollView()
    label = Label(text=f"❌ 启动严重错误:\n\n{error_msg}", 
                  color=(1, 0, 0, 1), 
                  font_size='16sp',
                  size_hint_y=None, 
                  text_size=(Window.width - 20, None))
    # 自动调整高度
    label.bind(texture_size=label.setter('size'))
    layout.add_widget(label)
    
    runTouchApp(layout)

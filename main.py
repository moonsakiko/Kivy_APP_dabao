import traceback
from kivy.app import runTouchApp
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window

# 设置深色背景以便看清报错
Window.clearcolor = (0.1, 0.1, 0.1, 1)

try:
    # ================= 核心代码 =================
    import os
    from kivy.app import App
    from kivy.clock import Clock
    from kivy.core.text import LabelBase
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.floatlayout import FloatLayout
    from kivy.uix.button import ButtonBehavior
    from kivy.uix.textinput import TextInput
    from kivy.uix.progressbar import ProgressBar
    from kivy.utils import platform
    from kivy.graphics import Color, RoundedRectangle, Rectangle

    # 尝试加载字体
    try:
        LabelBase.register(name='Roboto', fn_regular='font.ttf')
        LabelBase.register(name='Roboto-Bold', fn_regular='font.ttf')
        has_font = True
    except:
        has_font = False

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

    # ❗❗❗ 关键修改：改名为 PDFButton，避开 ActionButton 关键词冲突 ❗❗❗
    class PDFButton(ButtonBehavior, FloatLayout):
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
            if platform == 'android':
                Clock.schedule_once(self.bind_android, 1)

            root = FloatLayout()
            with root.canvas.before:
                Color(0.96, 0.96, 0.98, 1)
                Rectangle(size=(3000, 3000), pos=(0,0))

            layout = BoxLayout(orientation='vertical', padding='20dp', spacing='15dp')
            f_args = {'font_name': 'font.ttf'} if has_font else {}

            # 标题
            title = Label(text="PDF 工具箱", font_size='28sp', color=(0.1,0.1,0.1,1), bold=True, size_hint_y=None, height='60dp', **f_args)
            layout.add_widget(title)

            if not has_font:
                layout.add_widget(Label(text="警告: 字体未加载", color=(1,0,0,1), size_hint_y=None, height='20dp'))

            # 卡片区
            card = Card(orientation='vertical', size_hint_y=None, height='220dp', spacing='10dp')
            
            # 使用新改名的 PDFButton
            self.path_btn = PDFButton(text="点击选择 PDF", bg_color=(0.9, 0.95, 1, 1), text_color=(0.2, 0.4, 0.8, 1))
            self.path_btn.bind(on_release=self.open_picker)
            card.add_widget(self.path_btn)
            
            self.input = TextInput(multiline=False, size_hint_y=None, height='50dp', hint_text="页码 (如 1-5)", **f_args)
            card.add_widget(self.input)
            layout.add_widget(card)

            # 执行按钮
            btn = PDFButton(text="执行提取", bg_color=(0.1, 0.7, 0.4, 1))
            btn.bind(on_release=self.do_extract)
            layout.add_widget(btn)

            # 进度与日志
            self.prog = ProgressBar(max=100, value=0, size_hint_y=None, height='4dp', opacity=0)
            layout.add_widget(self.prog)

            self.console = Label(text="系统就绪...", color=(0.5,0.5,0.5,1), size_hint_y=None, height='300dp', text_size=(Window.width-40, None), halign='left', valign='top', **f_args)
            layout.add_widget(self.console)

            return root

        def log(self, msg):
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
                    from jnius import autoclass, cast
                    Intent = autoclass('android.content.Intent')
                    intent = Intent()
                    intent.setAction(Intent.ACTION_GET_CONTENT)
                    intent.setType("application/pdf")
                    
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
                    self.log(f"解析错误: {e}")

        def copy_file(self, uri):
            try:
                from jnius import autoclass, cast
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                act = cast('android.app.Activity', PythonActivity.mActivity)
                resolver = act.getContentResolver()
                inp = resolver.openInputStream(uri)
                
                cache = act.getCacheDir().getAbsolutePath() + "/temp.pdf"
                
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
                self.path_btn.label.text = "✅ 文件已加载"
                self.path_btn.label.color = (0, 0.5, 0, 1)
                self.log("加载成功")
            except Exception as e:
                self.log(f"IO错误: {e}")

        def do_extract(self, *args):
            if not self.cached_pdf_path: return self.log("请先选择文件")
            try:
                from pypdf import PdfReader, PdfWriter
                reader = PdfReader(self.cached_pdf_path)
                writer = PdfWriter()
                
                # 极简解析逻辑，确保不崩
                s_str = self.input.text
                if not s_str: return self.log("请输入页码")
                
                indices = []
                for p in s_str.replace(' ','').split(','):
                    if '-' in p:
                        s, e = p.split('-')
                        indices.extend(range(int(s)-1, int(e)))
                    else:
                        indices.append(int(p)-1)

                writer.append(fileobj=self.cached_pdf_path, pages=indices)
                
                out = "/storage/emulated/0/Download/Extract_Result.pdf"
                with open(out, "wb") as f:
                    writer.write(f)
                self.log(f"成功保存在 Download:\n{out}")
            except Exception as e:
                self.log(f"提取失败: {e}")

    PDFApp().run()

except Exception as e:
    # 黑匣子捕获报错
    error_msg = traceback.format_exc()
    layout = ScrollView()
    label = Label(text=f"❌ 错误:\n\n{error_msg}", color=(1,0,0,1), size_hint_y=None)
    label.bind(texture_size=label.setter('size'))
    layout.add_widget(label)
    runTouchApp(layout)

import os
import datetime
import traceback
from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.core.text import LabelBase
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button, ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.utils import platform
from kivy.graphics import Color, RoundedRectangle, Rectangle

# --- 字体注入 ---
try:
    LabelBase.register(name='Roboto', fn_regular='font.ttf')
    LabelBase.register(name='Roboto-Bold', fn_regular='font.ttf')
except:
    pass

# --- UI 组件 (保持你的美观布局) ---
class Card(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.padding = '20dp'
        with self.canvas.before:
            Color(0.9, 0.9, 0.92, 1) # 边框色
            self.border = RoundedRectangle(size=self.size, pos=self.pos, radius=[16,])
            Color(1, 1, 1, 1) # 内容色
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
        self.label = Label(text=text, pos_hint={'center_x': .5, 'center_y': .5}, 
                           font_size='18sp', bold=True, color=text_color)
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
        # 延迟绑定，防止启动时 JNI 未就绪导致闪退
        if platform == 'android':
            Clock.schedule_once(self.bind_android_callback, 1)

        root = FloatLayout()
        with root.canvas.before:
            Color(0.97, 0.97, 0.98, 1)
            Rectangle(size=(3000, 3000), pos=(0,0))

        layout = BoxLayout(orientation='vertical', padding='24dp', spacing='15dp')
        
        # 标题
        header = BoxLayout(orientation='vertical', size_hint_y=None, height='70dp')
        title = Label(text="PDF 工具箱", font_size='28sp', color=(0.1, 0.1, 0.1, 1), bold=True, halign='left', size_hint_x=None, width='300dp')
        title.bind(texture_size=title.setter('size'))
        header.add_widget(title)
        layout.add_widget(header)

        # 操作卡片
        main_card = Card(orientation='vertical', size_hint_y=None, height='260dp', spacing='15dp')
        
        main_card.add_widget(Label(text="步骤 1: 选择文件", color=(0.5,0.5,0.5,1), size_hint_y=None, height='20dp', halign='left', text_size=(500, None)))
        self.path_btn = ActionButton(text="点击选择 PDF", bg_color=(0.93, 0.95, 0.97, 1), text_color=(0.2, 0.4, 0.7, 1))
        self.path_btn.bind(on_release=self.open_android_picker)
        main_card.add_widget(self.path_btn)
        
        main_card.add_widget(Label(text="步骤 2: 输入范围 (如 1-5)", color=(0.5,0.5,0.5,1), size_hint_y=None, height='20dp', halign='left', text_size=(500, None)))
        self.range_input = TextInput(multiline=False, size_hint_y=None, height='50dp', hint_text="在此输入...", background_color=(0.98,0.98,0.99,1), cursor_color=(0,0,0,1))
        main_card.add_widget(self.range_input)
        
        layout.add_widget(main_card)

        # 执行按钮
        btn_run = ActionButton(text="开始提取", bg_color=(0.1, 0.65, 0.3, 1))
        btn_run.bind(on_release=self.do_extract)
        layout.add_widget(btn_run)

        # 进度条
        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height='4dp', opacity=0)
        layout.add_widget(self.progress)

        # 日志
        log_scroll = ScrollView(size_hint_y=1)
        self.console_log = Label(text="系统就绪...", color=(0.6, 0.6, 0.65, 1), font_size='13sp', size_hint_y=None, halign='left', valign='top', markup=True)
        self.console_log.bind(texture_size=self.console_log.setter('size'))
        self.console_log.bind(width=lambda instance, value: setattr(instance, 'text_size', (value, None)))
        log_scroll.add_widget(self.console_log)
        layout.add_widget(log_scroll)

        root.add_widget(layout)
        return root

    def log(self, msg, level="INFO"):
        color = "666666"
        if level == "ERROR": color = "ff4444"
        elif level == "SUCCESS": color = "00aa44"
        self.console_log.text = f"[color=#{color}]• {str(msg)}[/color]\n" + self.console_log.text

    # --- 修复后的 Android 逻辑 ---
    
    def bind_android_callback(self, dt):
        try:
            from android import activity
            activity.bind(on_activity_result=self.on_android_result)
        except:
            self.log("非安卓环境", "WARN")

    def open_android_picker(self, *args):
        if platform == 'android':
            try:
                # ❗局部导入 jnius，防止全局加载崩溃
                from jnius import autoclass, cast
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
                Intent = autoclass('android.content.Intent')

                intent = Intent()
                intent.setAction(Intent.ACTION_GET_CONTENT)
                intent.setType("application/pdf")
                # ❗最原始的调用，不加 createChooser 标题，防止 JNI 字符串崩溃
                currentActivity.startActivityForResult(intent, 101)
                self.log("正在打开...")
            except Exception as e:
                self.log(f"启动失败: {e}", "ERROR")

    def on_android_result(self, requestCode, resultCode, intent):
        if requestCode == 101 and resultCode == -1 and intent:
            try:
                # ❗局部导入，防止引用泄漏
                from jnius import autoclass, cast
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
                
                uri = intent.getData()
                self.log("文件已选择，正在解析...")
                
                # 简单的流复制
                resolver = currentActivity.getContentResolver()
                input_stream = resolver.openInputStream(uri)
                cache_dir = currentActivity.getCacheDir().getAbsolutePath()
                output_path = os.path.join(cache_dir, "temp.pdf")
                
                FileOutputStream = autoclass('java.io.FileOutputStream')
                output_stream = FileOutputStream(output_path)
                
                # 降低 buffer 大小，防止内存压力
                byte_arr = bytearray(1024 * 64) 
                while True:
                    n = input_stream.read(byte_arr)
                    if n <= 0: break
                    output_stream.write(byte_arr[:n])
                
                input_stream.close()
                output_stream.close()
                
                self.cached_pdf_path = output_path
                self.path_btn.label.text = "✅ 文件已加载"
                self.path_btn.label.color = (0.1, 0.5, 0.2, 1)
                self.log("加载成功！", "SUCCESS")
                
            except Exception as e:
                self.log(f"解析文件失败: {e}", "ERROR")
        else:
            self.log("未选择文件")

    # --- 提取逻辑 ---
    def do_extract(self, *args):
        if not self.cached_pdf_path:
            self.log("请先选择文件", "ERROR")
            return
        range_str = self.range_input.text
        if not range_str:
            self.log("请输入页码", "ERROR")
            return

        self.progress.opacity = 1
        self.progress.value = 10
        Clock.schedule_once(lambda dt: self._process(range_str), 0.1)

    def _process(self, range_str):
        try:
            from pypdf import PdfReader, PdfWriter
            self.progress.value = 30
            reader = PdfReader(self.cached_pdf_path)
            writer = PdfWriter()
            
            indices = []
            parts = range_str.replace(' ', '').split(',')
            for part in parts:
                if '-' in part:
                    s, e = part.split('-')
                    start = int(s) - 1
                    end = len(reader.pages) if e.lower() == 'end' else int(e)
                    indices.extend(range(start, end))
                else:
                    indices.append(int(part)-1)

            writer.append(fileobj=self.cached_pdf_path, pages=indices)
            
            save_dir = "/storage/emulated/0/Download"
            out_path = os.path.join(save_dir, "PDF_Result.pdf")
            c = 1
            while os.path.exists(out_path):
                out_path = os.path.join(save_dir, f"PDF_Result_{c}.pdf")
                c += 1
            
            with open(out_path, "wb") as f:
                writer.write(f)
            
            self.progress.value = 100
            self.log(f"成功！已保存到 Download", "SUCCESS")
            Clock.schedule_once(lambda dt: setattr(self.progress, 'opacity', 0), 3)
            
        except Exception as e:
            self.log(f"处理出错: {e}", "ERROR")
            self.progress.opacity = 0

if __name__ == '__main__':
    try:
        PDFApp().run()
    except Exception as e:
        print(e)

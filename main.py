# ❗ 这是一个没有任何美化的纯净版本，用于测试内核功能
import os
import traceback
from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.utils import platform

# 尝试加载字体，失败则忽略
try:
    LabelBase.register(name='Roboto', fn_regular='font.ttf')
    LabelBase.register(name='Roboto-Bold', fn_regular='font.ttf')
    FONT_NAME = 'font.ttf'
except:
    FONT_NAME = 'Roboto' # 回退到默认

class PDFApp(App):
    cached_pdf_path = None
    
    def build(self):
        # 延迟绑定安卓接口
        if platform == 'android':
            Clock.schedule_once(self.bind_android, 1)
        
        # 根布局：垂直排列
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        # 1. 标题
        self.layout.add_widget(Label(
            text="PDF工具箱 (安全模式)", 
            font_size='24sp', 
            size_hint_y=None, 
            height=100,
            font_name=FONT_NAME
        ))

        # 2. 状态显示区
        self.status_label = Label(
            text="系统初始化完成\n等待操作...", 
            color=(0, 1, 0, 1),
            font_name=FONT_NAME,
            halign='center'
        )
        self.layout.add_widget(self.status_label)

        # 3. 选择文件按钮 (原生丑按钮，但最稳)
        self.btn_select = Button(
            text="[1] 选择 PDF 文件",
            size_hint_y=None,
            height=120,
            background_color=(0.2, 0.6, 1, 1),
            font_name=FONT_NAME
        )
        self.btn_select.bind(on_release=self.open_picker)
        self.layout.add_widget(self.btn_select)

        # 4. 页码输入框
        self.input_range = TextInput(
            hint_text="[2] 输入页码 (如 1-5)",
            size_hint_y=None,
            height=100,
            multiline=False,
            font_name=FONT_NAME
        )
        self.layout.add_widget(self.input_range)

        # 5. 执行按钮
        self.btn_run = Button(
            text="[3] 开始提取",
            size_hint_y=None,
            height=120,
            background_color=(0, 0.8, 0.2, 1),
            font_name=FONT_NAME
        )
        self.btn_run.bind(on_release=self.do_extract)
        self.layout.add_widget(self.btn_run)

        # 6. 底部日志区
        self.log_view = TextInput(
            text="日志区域 ready...",
            readonly=True,
            size_hint_y=0.4,
            background_color=(0.1, 0.1, 0.1, 1),
            foreground_color=(0.8, 0.8, 0.8, 1),
            font_name=FONT_NAME
        )
        self.layout.add_widget(self.log_view)

        return self.layout

    def log(self, msg):
        print(f"APP_LOG: {msg}")
        self.log_view.text = f"• {str(msg)}\n" + self.log_view.text

    # --- 安卓底层逻辑 ---
    def bind_android(self, dt):
        try:
            from android import activity
            activity.bind(on_activity_result=self.on_result)
            self.log("安卓接口绑定成功")
        except:
            self.log("非安卓环境，跳过绑定")

    def open_picker(self, *args):
        if platform == 'android':
            try:
                # 局部引用，防止内存泄漏
                from jnius import autoclass, cast
                Intent = autoclass('android.content.Intent')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
                
                intent = Intent()
                intent.setAction(Intent.ACTION_GET_CONTENT)
                intent.setType("application/pdf")
                currentActivity.startActivityForResult(intent, 101)
                self.log("正在唤起系统文件选择器...")
            except Exception as e:
                self.log(f"启动失败: {e}")
                self.log(traceback.format_exc())

    def on_result(self, req, res, intent):
        if req == 101:
            if res == -1 and intent:
                try:
                    uri = intent.getData()
                    self.copy_file(uri)
                except Exception as e:
                    self.log(f"解析URI失败: {e}")
            else:
                self.log("用户取消了选择")

    def copy_file(self, uri):
        try:
            from jnius import autoclass, cast
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            act = cast('android.app.Activity', PythonActivity.mActivity)
            
            resolver = act.getContentResolver()
            inp = resolver.openInputStream(uri)
            
            cache = act.getCacheDir().getAbsolutePath() + "/temp_target.pdf"
            
            FileOutputStream = autoclass('java.io.FileOutputStream')
            out = FileOutputStream(cache)
            
            # 极简 buffer copy
            buf = bytearray(4096)
            while True:
                n = inp.read(buf)
                if n <= 0: break
                out.write(buf[:n])
            
            inp.close()
            out.close()
            
            self.cached_pdf_path = cache
            self.btn_select.text = "✅ 文件已就绪"
            self.btn_select.background_color = (0, 0.5, 0, 1)
            self.log("文件加载成功！")
            
        except Exception as e:
            self.log(f"文件拷贝错误: {e}")

    def do_extract(self, *args):
        if not self.cached_pdf_path:
            self.log("错误：请先选择文件")
            return
        
        raw_range = self.input_range.text
        if not raw_range:
            self.log("错误：请输入页码")
            return

        try:
            from pypdf import PdfReader, PdfWriter
            self.log("正在分析 PDF...")
            reader = PdfReader(self.cached_pdf_path)
            writer = PdfWriter()
            
            # 解析页码
            indices = []
            for part in raw_range.replace(' ', '').split(','):
                if '-' in part:
                    s, e = part.split('-')
                    start = int(s) - 1
                    end = len(reader.pages) if e.lower() == 'end' else int(e)
                    indices.extend(range(start, end))
                else:
                    indices.append(int(part)-1)

            writer.append(fileobj=self.cached_pdf_path, pages=indices)
            
            out_path = "/storage/emulated/0/Download/PDF_Safe_Result.pdf"
            with open(out_path, "wb") as f:
                writer.write(f)
            
            self.log(f"成功！已保存至 Download")
            
        except Exception as e:
            self.log(f"提取失败: {e}")
            self.log(traceback.format_exc())

if __name__ == '__main__':
    # 这里不做 try-except，让 Kivy 自己处理错误
    # 如果白屏，说明 Kivy 引擎启动了但没画出来
    PDFApp().run()

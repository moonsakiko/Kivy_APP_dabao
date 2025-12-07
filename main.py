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

# --- 1. 字体注入 ---
# 必须上传 font.ttf
try:
    LabelBase.register(name='Roboto', fn_regular='font.ttf')
    LabelBase.register(name='Roboto-Bold', fn_regular='font.ttf')
except:
    pass

# --- 2. 安卓原生接口 ---
if platform == 'android':
    from jnius import autoclass, cast
    from android import activity
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
    Intent = autoclass('android.content.Intent')
    Context = autoclass('android.content.Context')

# --- 3. UI 组件 ---

class Card(BoxLayout):
    """带边框的圆角卡片"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.padding = '20dp'
        with self.canvas.before:
            # 边框阴影
            Color(0.85, 0.85, 0.88, 1)
            self.border = RoundedRectangle(size=self.size, pos=self.pos, radius=[16,])
            # 内容背景
            Color(1, 1, 1, 1)
            self.rect = RoundedRectangle(size=(self.width, self.height-2), pos=(self.x, self.y+1), radius=[15,])
            
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.border.pos = instance.pos
        self.border.size = instance.size
        self.rect.pos = (instance.x + 1, instance.y + 1)
        self.rect.size = (instance.width - 2, instance.height - 2)

class ActionButton(ButtonBehavior, FloatLayout):
    """大圆角按钮"""
    def __init__(self, text="", bg_color=(0.2, 0.6, 1, 1), text_color=(1,1,1,1), **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = '60dp'
        self.bg_color = bg_color
        
        with self.canvas.before:
            self.color_node = Color(*bg_color)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[12,])
        
        # 移除 font_name='font.ttf' 这里，依靠全局替换，避免未加载报错
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

# --- 4. 主程序 ---
class PDFApp(App):
    cached_pdf_path = None 
    
    def build(self):
        if platform == 'android':
            activity.bind(on_activity_result=self.on_android_result)

        # 根布局：浅灰背景
        root = FloatLayout()
        with root.canvas.before:
            Color(0.96, 0.97, 0.98, 1)
            Rectangle(size=(3000, 3000), pos=(0,0))

        layout = BoxLayout(orientation='vertical', padding='24dp', spacing='20dp')
        
        # --- 标题栏 ---
        header = BoxLayout(orientation='vertical', size_hint_y=None, height='80dp', spacing='5dp')
        title = Label(text="PDF 工具箱", font_size='32sp', color=(0.1, 0.15, 0.2, 1), 
                      bold=True, size_hint_x=None, width='300dp', halign='left')
        subtitle = Label(text="简洁 高效 稳定", font_size='14sp', color=(0.5, 0.5, 0.6, 1),
                         size_hint_x=None, width='300dp', halign='left')
        title.bind(texture_size=title.setter('size'))
        header.add_widget(title)
        header.add_widget(subtitle)
        layout.add_widget(header)

        # --- 核心操作区 ---
        main_card = Card(orientation='vertical', size_hint_y=None, height='280dp', spacing='15dp')
        
        # 1. 文件按钮
        lbl_file = Label(text="第一步: 选择文件", color=(0.4,0.4,0.4,1), size_hint_y=None, height='20dp', halign='left', text_size=(500, None))
        main_card.add_widget(lbl_file)
        
        self.path_btn = ActionButton(text="点击选择 PDF 文件", bg_color=(0.92, 0.94, 0.96, 1), text_color=(0.2, 0.4, 0.7, 1))
        self.path_btn.bind(on_release=self.open_android_picker)
        main_card.add_widget(self.path_btn)
        
        # 2. 页码输入
        lbl_range = Label(text="第二步: 输入页码 (如 1-5, 8)", color=(0.4,0.4,0.4,1), size_hint_y=None, height='20dp', halign='left', text_size=(500, None))
        main_card.add_widget(lbl_range)
        
        self.range_input = TextInput(
            multiline=False, size_hint_y=None, height='50dp',
            hint_text="点击此处输入...",
            background_color=(0.98, 0.98, 0.99, 1), cursor_color=(0,0,0,1),
            padding=[15, 15]
        )
        main_card.add_widget(self.range_input)
        
        layout.add_widget(main_card)

        # --- 开始按钮 ---
        btn_run = ActionButton(text="开始提取", bg_color=(0.2, 0.4, 0.85, 1))
        btn_run.bind(on_release=self.do_extract)
        layout.add_widget(btn_run)

        # --- 进度条 ---
        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height='4dp', opacity=0)
        layout.add_widget(self.progress)

        # --- 日志区域 ---
        log_scroll = ScrollView(size_hint_y=1)
        self.console_log = Label(
            text="[系统] 准备就绪", 
            color=(0.6, 0.6, 0.65, 1),
            font_size='13sp',
            size_hint_y=None,
            halign='left', valign='top',
            markup=True
        )
        self.console_log.bind(texture_size=self.console_log.setter('size'))
        self.console_log.bind(width=lambda instance, value: setattr(instance, 'text_size', (value, None)))
        
        log_scroll.add_widget(self.console_log)
        layout.add_widget(log_scroll)

        root.add_widget(layout)
        return root

    def log(self, msg, level="INFO"):
        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        color_hex = "666666"
        if level == "ERROR": color_hex = "ff4444"
        elif level == "SUCCESS": color_hex = "00aa44"
        
        # 使用 str() 强制转换，防止打印对象时报错
        safe_msg = str(msg)
        new_line = f"[color=#{color_hex}][b]• {safe_msg}[/b][/color]\n"
        self.console_log.text = new_line + self.console_log.text

    # --- 修复后的 Android 原生选择 ---
    def open_android_picker(self, *args):
        if platform == 'android':
            try:
                # 简化 Intent，去除 createChooser，防止 LocalRef 错误
                intent = Intent()
                intent.setAction(Intent.ACTION_GET_CONTENT)
                intent.setType("application/pdf")
                # 不添加 Category，防止部分机型不兼容
                currentActivity.startActivityForResult(intent, 101)
                self.log("正在打开系统选择器...")
            except Exception as e:
                self.log(f"启动失败: {str(e)}", "ERROR")

    def on_android_result(self, requestCode, resultCode, intent):
        try:
            if requestCode == 101:
                if resultCode == -1 and intent is not None: # RESULT_OK
                    uri = intent.getData()
                    self.copy_uri_to_cache(uri)
                else:
                    self.log("未选择文件", "INFO")
        except Exception as e:
            self.log(f"回调错误: {str(e)}", "ERROR")

    def copy_uri_to_cache(self, uri):
        try:
            self.log("正在读取文件...")
            resolver = currentActivity.getContentResolver()
            input_stream = resolver.openInputStream(uri)
            
            # 临时文件
            cache_dir = currentActivity.getCacheDir().getAbsolutePath()
            output_path = os.path.join(cache_dir, "temp_target.pdf")
            
            # 使用 Java 流进行复制 (最稳妥的方式)
            FileOutputStream = autoclass('java.io.FileOutputStream')
            output_stream = FileOutputStream(output_path)
            
            # 手动 Buffer 复制，避免 jnius 传递大对象卡死
            # 我们这里分块读取，但为了避免 jnius byte[] 转换的复杂性
            # 我们尝试直接读完 (如果文件不是特别巨大的话，通常没问题)
            # 或者，更简单：告诉用户我们成功了，让 pypdf 直接读 uri? 不行 pypdf 不支持 uri
            
            # 采用 Kivy 社区推荐的简易复制法
            byte_arr = bytearray(1024 * 256) # 256KB 缓存
            while True:
                n = input_stream.read(byte_arr)
                if n <= 0: break
                output_stream.write(byte_arr[:n])
            
            input_stream.close()
            output_stream.close()
            
            self.cached_pdf_path = output_path
            
            # 更新界面
            self.path_btn.label.text = "已加载 PDF 文件"
            self.path_btn.label.color = (0.1, 0.6, 0.3, 1) # 绿色文字
            self.log("文件加载成功！", "SUCCESS")
            
        except Exception as e:
            self.log(f"解析错误: {str(e)}", "ERROR")

    # --- 提取逻辑 ---
    def do_extract(self, *args):
        if not self.cached_pdf_path or not os.path.exists(self.cached_pdf_path):
            self.log("请先选择文件", "ERROR")
            return

        range_str = self.range_input.text
        if not range_str:
            self.log("请输入页码范围", "ERROR")
            return

        self.progress.opacity = 1
        self.progress.value = 10
        self.log("正在处理...", "INFO")
        
        Clock.schedule_once(lambda dt: self._process(range_str), 0.1)

    def _process(self, range_str):
        try:
            from pypdf import PdfReader, PdfWriter
            self.progress.value = 20
            
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

            self.progress.value = 60
            writer.append(fileobj=self.cached_pdf_path, pages=indices)
            
            save_dir = "/storage/emulated/0/Download"
            out_path = os.path.join(save_dir, "PDF提取结果.pdf")
            
            c = 1
            while os.path.exists(out_path):
                out_path = os.path.join(save_dir, f"PDF提取结果_{c}.pdf")
                c += 1
            
            self.progress.value = 90
            with open(out_path, "wb") as f:
                writer.write(f)
            
            self.progress.value = 100
            self.log(f"成功！已保存至 Download 文件夹", "SUCCESS")
            
            # 延迟隐藏
            Clock.schedule_once(lambda dt: setattr(self.progress, 'opacity', 0), 3)
            
        except Exception as e:
            self.log(f"处理失败: {str(e)}", "ERROR")
            self.progress.opacity = 0

if __name__ == '__main__':
    try:
        PDFApp().run()
    except Exception as e:
        print(e)

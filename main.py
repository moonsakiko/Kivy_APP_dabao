import os
import shutil
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
from kivy.uix.scrollview import ScrollView
from kivy.utils import platform
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.properties import StringProperty

# --- 1. 字体注入 ---
try:
    LabelBase.register(name='Roboto', fn_regular='font.ttf')
    LabelBase.register(name='Roboto-Bold', fn_regular='font.ttf')
except:
    pass

# --- 2. 安卓原生接口 (黑科技区) ---
if platform == 'android':
    from jnius import autoclass, cast
    from android import activity, mActivity
    
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
    Context = autoclass('android.content.Context')
    Intent = autoclass('android.content.Intent')
    Uri = autoclass('android.net.Uri')
    ContentResolver = currentActivity.getContentResolver()

# --- 3. UI 组件 ---

class Card(BoxLayout):
    """白色圆角卡片"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.padding = '15dp'
        with self.canvas.before:
            Color(1, 1, 1, 1)
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
        self.height = '50dp'
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

# --- 4. 主程序 ---
class PDFApp(App):
    # 用于存储临时复制过来的文件路径
    cached_pdf_path = None 
    
    def build(self):
        # 绑定安卓的回调监听
        if platform == 'android':
            activity.bind(on_activity_result=self.on_android_result)

        # 根布局：苹果风浅灰背景 (#F5F5F7)
        root = FloatLayout()
        with root.canvas.before:
            Color(0.96, 0.96, 0.97, 1)
            Rectangle(size=(3000, 3000), pos=(0,0))

        layout = BoxLayout(orientation='vertical', padding='20dp', spacing='15dp')
        
        # 标题
        title = Label(
            text="PDF 大师 v8.0", 
            font_size='22sp', 
            color=(0.1, 0.1, 0.1, 1), 
            size_hint_y=None, 
            height='40dp', 
            font_name='font.ttf', 
            bold=True
        )
        layout.add_widget(title)

        # --- 卡片 1：选择文件 ---
        card1 = Card(orientation='vertical', size_hint_y=None, height='140dp', spacing='10dp')
        
        self.path_display = TextInput(
            text="等待选择...", readonly=True, background_color=(0.95, 0.95, 0.95, 1), 
            foreground_color=(0.5, 0.5, 0.5, 1), font_name='font.ttf', 
            multiline=False, size_hint_y=None, height='35dp'
        )
        card1.add_widget(self.path_display)
        
        btn_select = ColorButton(text="📂 调用系统文件选择", bg_color=(0, 0.48, 1, 1))
        btn_select.bind(on_release=self.open_android_picker)
        card1.add_widget(btn_select)
        layout.add_widget(card1)

        # --- 卡片 2：操作 ---
        card2 = Card(orientation='vertical', size_hint_y=None, height='140dp', spacing='10dp')
        
        self.range_input = TextInput(
            multiline=False, size_hint_y=None, height='40dp',
            font_name='font.ttf', hint_text="输入页码 (如 1-5, 8)"
        )
        card2.add_widget(self.range_input)
        
        btn_run = ColorButton(text="🚀 开始提取", bg_color=(0, 0.7, 0.3, 1))
        btn_run.bind(on_release=self.do_extract)
        card2.add_widget(btn_run)
        layout.add_widget(card2)

        # --- 进度条 ---
        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height='5dp', opacity=0)
        layout.add_widget(self.progress)

        # --- 卡片 3：控制台日志 (你要的功能) ---
        log_card = Card(orientation='vertical')
        
        lbl_log_title = Label(text="运行日志", color=(0.5,0.5,0.5,1), size_hint_y=None, height='20dp', font_name='font.ttf', halign='left')
        lbl_log_title.bind(size=lbl_log_title.setter('text_size'))
        log_card.add_widget(lbl_log_title)

        # 滚动区域
        scroll = ScrollView(bar_width='4dp')
        self.console_log = Label(
            text="[系统] 准备就绪...", 
            color=(0.2, 0.2, 0.2, 1), 
            font_name='font.ttf',
            font_size='12sp',
            size_hint_y=None,
            halign='left',
            valign='top'
        )
        self.console_log.bind(texture_size=self.console_log.setter('size'))
        scroll.add_widget(self.console_log)
        log_card.add_widget(scroll)
        
        layout.add_widget(log_card)
        
        root.add_widget(layout)
        return root

    def log(self, msg, level="INFO"):
        """向屏幕下方的控制台添加日志"""
        import datetime
        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        new_line = f"[{time_str}] [{level}] {msg}\n"
        self.console_log.text += new_line
        # 错误信息变红
        if level == "ERROR":
            self.path_display.text = "发生错误，请看日志"

    # --- 核心：Android 原生文件选择 ---
    def open_android_picker(self, *args):
        if platform == 'android':
            try:
                # 创建一个原生的 Android Intent
                intent = Intent(Intent.ACTION_GET_CONTENT)
                intent.setType("application/pdf") # 只选 PDF
                intent.addCategory(Intent.CATEGORY_OPENABLE)
                # 开启选择器，请求码设为 101
                currentActivity.startActivityForResult(Intent.createChooser(intent, "Select PDF"), 101)
                self.log("正在打开系统选择器...")
            except Exception as e:
                self.log(f"启动选择器失败: {e}", "ERROR")
        else:
            # 电脑端测试用
            self.log("非安卓环境，无法调用系统选择器", "WARN")

    # --- 核心：接收选择结果 ---
    def on_android_result(self, requestCode, resultCode, intent):
        if requestCode == 101 and resultCode == -1: # RESULT_OK
            if intent:
                uri = intent.getData()
                self.copy_uri_to_cache(uri)
                return
        self.log("未选择文件或取消", "WARN")

    def copy_uri_to_cache(self, uri):
        """将 content:// 转换为真实文件"""
        try:
            self.log("正在解析文件...")
            # 获取 ContentResolver
            resolver = currentActivity.getContentResolver()
            
            # 打开输入流
            input_stream = resolver.openInputStream(uri)
            
            # 确定文件名 (为了简单，我们用时间戳临时命名，或者尝试查询游标)
            # 这里直接重命名为 temp.pdf 方便处理
            cache_dir = currentActivity.getCacheDir().getAbsolutePath()
            output_path = os.path.join(cache_dir, "selected_temp.pdf")
            
            self.log(f"缓存路径: {output_path}")
            
            # 写入文件 (Python 方式写入)
            # 既然 input_stream 是 Java 对象，我们需要用 byte array 读取
            # 但更简单的办法是用 jnius 读取流
            
            # 这里使用一个简单粗暴的方法：
            # 我们无法直接把 Java InputStream 转给 Python，
            # 所以我们用 Python 的 open 读取，这在 Kivy 里有时候行不通
            # 让我们用纯 Java 方式复制
            
            FileUtils = autoclass('android.os.FileUtils') # API 29+
            # 考虑到兼容性，我们手写 buffer copy
            
            FileOutputStream = autoclass('java.io.FileOutputStream')
            output_stream = FileOutputStream(output_path)
            
            # Java 9+ 有 transferTo，但在安卓上可能要手动读写
            # 这是一个简单的 buffer copy 循环
            buffer = bytearray(4096)
            while True:
                read = input_stream.read(buffer)
                if read == -1:
                    break
                # 将 java byte array 写入 output
                # 注意：jnius 的 buffer 处理比较复杂，我们用最傻瓜的方式
                # 实际上 input_stream.read() 返回 int，需要处理
                # 为了稳妥，我们不用 buffer，虽然慢点
                # 等等，input_stream.read(buffer) 在 jnius 可能报错
                
                # ✅ 替代方案：直接在 Python 里读 content:// 是不行的
                # 我们必须相信 plyer 还是有用的？不，plyer 失败了
                
                # 让我们用最最基础的 Java IOUtil 思想
                pass
                # 由于 jnius 写流太复杂，我们简化逻辑：
                # 假设用户选了文件，我们提示用户：
                break 

            # ⬆️ 上面的流操作太容易崩，我们换个思路
            # 使用 Kivy 社区验证过的代码片段
            
            self.log("正在通过 Java 流复制文件...")
            # 重新获取流
            input_stream = resolver.openInputStream(uri)
            output_stream = FileOutputStream(output_path)
            
            # 极简复制法
            byte_arr = bytearray(1024 * 1024) # 1MB buffer
            while True:
                n = input_stream.read(byte_arr)
                if n <= 0: break
                # 将读取到的部分写入
                # jnius 传递 byte array 有时候会有问题
                # 但 FileOutputStream.write(byte[]) 是支持的
                # 我们需要把 python bytearray 截取
                output_stream.write(byte_arr[:n])
            
            input_stream.close()
            output_stream.close()
            
            self.cached_pdf_path = output_path
            self.path_display.text = "已就绪 (temp.pdf)"
            self.log("✅ 文件解析成功！已缓存", "SUCCESS")
            
        except Exception as e:
            self.log(f"文件解析失败: {e}", "ERROR")
            traceback.print_exc()

    # --- 提取逻辑 ---
    def do_extract(self, *args):
        if not self.cached_pdf_path or not os.path.exists(self.cached_pdf_path):
            self.log("❌ 请先选择文件", "ERROR")
            return

        range_str = self.range_input.text
        if not range_str:
            self.log("❌ 请输入页码", "ERROR")
            return

        self.progress.opacity = 1
        self.progress.value = 10
        self.log("开始任务...", "INFO")
        
        Clock.schedule_once(lambda dt: self._process(range_str), 0.1)

    def _process(self, range_str):
        try:
            from pypdf import PdfReader, PdfWriter
            self.progress.value = 30
            self.log("正在读取 PDF 结构...")
            
            reader = PdfReader(self.cached_pdf_path)
            writer = PdfWriter()
            
            indices = []
            parts = range_str.replace(' ', '').split(',')
            for part in parts:
                if '-' in part:
                    s, e = part.split('-')
                    start = int(s) - 1
                    if e.lower() == 'end':
                        end = len(reader.pages)
                    else:
                        end = int(e)
                    indices.extend(range(start, end))
                    self.log(f"解析范围: {s} 到 {e}")
                else:
                    indices.append(int(part)-1)
                    self.log(f"解析单页: {part}")

            self.progress.value = 60
            self.log(f"正在提取 {len(indices)} 个页面...")
            writer.append(fileobj=self.cached_pdf_path, pages=indices)
            
            # 保存到 Download
            save_dir = "/storage/emulated/0/Download"
            out_path = os.path.join(save_dir, "extracted_result.pdf")
            
            # 防重名
            c = 1
            while os.path.exists(out_path):
                out_path = os.path.join(save_dir, f"extracted_result_{c}.pdf")
                c += 1
            
            self.progress.value = 80
            self.log("正在写入文件...")
            with open(out_path, "wb") as f:
                writer.write(f)
            
            self.progress.value = 100
            self.log(f"✅ 完成！保存在: {os.path.basename(out_path)}", "SUCCESS")
            self.path_display.text = "完成"
            
        except Exception as e:
            self.log(f"处理失败: {e}", "ERROR")
            self.progress.opacity = 0

if __name__ == '__main__':
    try:
        PDFApp().run()
    except Exception as e:
        print(e)

import os
import io
import time
import traceback
from datetime import datetime
from PIL import Image, ImageOps

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.togglebutton import ToggleButton
from kivy.utils import platform
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.core.window import Window

# --- 0. 基础配置与字体 ---
# 必须要有 font.ttf 否则中文乱码
try:
    LabelBase.register(name='Roboto', fn_regular='font.ttf')
    LabelBase.register(name='Roboto-Bold', fn_regular='font.ttf')
    HAS_FONT = True
    FONT_NAME = 'Roboto'
except:
    HAS_FONT = False
    FONT_NAME = 'Roboto' # 即使失败也保留变量名防崩

# 设置背景色 (深灰护眼)
Window.clearcolor = (0.95, 0.96, 0.98, 1)

# --- 1. UI 组件库 (复用高颜值组件) ---

class ImgCard(BoxLayout):
    """带阴影和圆角的卡片容器"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.padding = '15dp'
        self.spacing = '10dp'
        with self.canvas.before:
            Color(0.9, 0.9, 0.92, 1) # 边框阴影
            self.border = RoundedRectangle(size=self.size, pos=self.pos, radius=[18,])
            Color(1, 1, 1, 1) # 内容白底
            self.rect = RoundedRectangle(size=(self.width, self.height-2), pos=(self.x, self.y+1), radius=[16,])
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.border.pos = instance.pos
        self.border.size = instance.size
        self.rect.pos = (instance.x + 1, instance.y + 1)
        self.rect.size = (instance.width - 2, instance.height - 2)

class ImgButton(ButtonBehavior, FloatLayout):
    """自定义圆角按钮"""
    def __init__(self, text="", bg_color=(0.2, 0.6, 1, 1), font_size='16sp', **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = '55dp'
        self.bg_color = bg_color
        
        with self.canvas.before:
            self.color_node = Color(*bg_color)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[10,])
        
        self.label = Label(text=text, pos_hint={'center_x': .5, 'center_y': .5}, 
                           font_size=font_size, bold=True, color=(1,1,1,1), font_name=FONT_NAME)
        self.add_widget(self.label)
        self.bind(size=self._update, pos=self._update)

    def _update(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def on_press(self):
        self.color_node.rgba = [c*0.8 for c in self.bg_color]
    def on_release(self):
        self.color_node.rgba = self.bg_color

class ImgOptionBtn(ToggleButton):
    """选项开关按钮"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0.9, 0.9, 0.9, 1)
        self.color = (0.4, 0.4, 0.4, 1)
        self.font_name = FONT_NAME
        self.group = 'compress_mode'
        self.allow_no_selection = False

    def on_state(self, widget, value):
        if value == 'down':
            self.background_color = (0.2, 0.6, 1, 1)
            self.color = (1, 1, 1, 1)
        else:
            self.background_color = (0.9, 0.9, 0.9, 1)
            self.color = (0.4, 0.4, 0.4, 1)

# --- 2. 核心逻辑类 ---

class ImageCompressorApp(App):
    # 状态变量
    selected_files = [] # 存储缓存后的文件路径
    
    def build(self):
        if platform == 'android':
            Clock.schedule_once(self.bind_android, 1)

        # 根布局
        root = FloatLayout()
        
        # 主滚动容器
        scroll = ScrollView(size_hint=(1, 1))
        layout = BoxLayout(orientation='vertical', padding='20dp', spacing='15dp', size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))

        # --- 标题栏 ---
        header = BoxLayout(orientation='vertical', size_hint_y=None, height='70dp')
        title = Label(text="图片压缩工坊", font_size='28sp', color=(0.1, 0.1, 0.15, 1), 
                      bold=True, halign='left', size_hint_x=None, width='300dp', font_name=FONT_NAME)
        subtitle = Label(text="iTool 智能引擎 v4.0", font_size='14sp', color=(0.5, 0.5, 0.6, 1), 
                         halign='left', size_hint_x=None, width='300dp', font_name=FONT_NAME)
        header.add_widget(title)
        header.add_widget(subtitle)
        layout.add_widget(header)

        # --- 步骤 1: 选择文件 ---
        card1 = ImgCard(orientation='vertical', size_hint_y=None, height='140dp')
        card1.add_widget(Label(text="第一步: 选择图片", color=(0.3,0.3,0.3,1), size_hint_y=None, height='30dp', font_name=FONT_NAME, bold=True))
        
        self.status_label = Label(text="未选择文件", color=(0.6,0.6,0.6,1), font_size='13sp', font_name=FONT_NAME)
        card1.add_widget(self.status_label)

        self.btn_select = ImgButton(text="打开相册选择 (支持多选)", bg_color=(0.2, 0.7, 0.5, 1))
        self.btn_select.bind(on_release=self.open_picker)
        card1.add_widget(self.btn_select)
        layout.add_widget(card1)

        # --- 步骤 2: 压缩策略 ---
        card2 = ImgCard(orientation='vertical', size_hint_y=None, height='220dp')
        card2.add_widget(Label(text="第二步: 压缩模式", color=(0.3,0.3,0.3,1), size_hint_y=None, height='30dp', font_name=FONT_NAME, bold=True))

        # 模式选择网格
        grid = GridLayout(cols=3, spacing='10dp', size_hint_y=None, height='50dp')
        self.opt_balance = ImgOptionBtn(text="平衡", state='down') # 默认
        self.opt_extreme = ImgOptionBtn(text="WebP极致")
        self.opt_custom = ImgOptionBtn(text="指定大小")
        
        # 绑定点击事件来切换显示
        self.opt_balance.bind(on_release=lambda x: self.toggle_options('balance'))
        self.opt_extreme.bind(on_release=lambda x: self.toggle_options('extreme'))
        self.opt_custom.bind(on_release=lambda x: self.toggle_options('custom'))

        grid.add_widget(self.opt_balance)
        grid.add_widget(self.opt_extreme)
        grid.add_widget(self.opt_custom)
        card2.add_widget(grid)

        # 动态参数区
        self.param_layout = BoxLayout(orientation='vertical', spacing='5dp')
        self.lbl_hint = Label(text="推荐模式：智能压缩 jpg/png，平衡画质与体积", color=(0.5,0.5,0.5,1), font_size='12sp', font_name=FONT_NAME)
        self.param_layout.add_widget(self.lbl_hint)
        
        # 指定大小输入框 (默认隐藏)
        self.input_size = TextInput(hint_text="输入目标大小 (如 500)", multiline=False, size_hint_y=None, height='0dp', opacity=0, input_filter='int', font_name=FONT_NAME)
        self.param_layout.add_widget(self.input_size)
        
        card2.add_widget(self.param_layout)
        layout.add_widget(card2)

        # --- 步骤 3: 执行 ---
        self.btn_run = ImgButton(text="开始批量处理", bg_color=(0.1, 0.4, 0.9, 1))
        self.btn_run.bind(on_release=self.start_processing)
        layout.add_widget(self.btn_run)

        # 进度条
        self.prog = ProgressBar(max=100, value=0, size_hint_y=None, height='10dp', opacity=0)
        layout.add_widget(self.prog)

        # --- 日志控制台 ---
        self.console = Label(text="[系统] 就绪...", color=(0.4, 0.4, 0.45, 1), font_size='12sp', 
                             size_hint_y=None, halign='left', valign='top', markup=True, font_name=FONT_NAME)
        self.console.bind(texture_size=self.console.setter('size'))
        self.console.bind(width=lambda instance, value: setattr(instance, 'text_size', (value, None)))
        layout.add_widget(self.console)

        scroll.add_widget(layout)
        root.add_widget(scroll)
        return root

    # --- 逻辑控制 ---
    def toggle_options(self, mode):
        if mode == 'balance':
            self.lbl_hint.text = "平衡模式: 限制宽1920px，质量80%，保留原格式"
            self.input_size.height = '0dp'
            self.input_size.opacity = 0
        elif mode == 'extreme':
            self.lbl_hint.text = "极致模式: 强制转 WebP，限制宽1280px，体积最小"
            self.input_size.height = '0dp'
            self.input_size.opacity = 0
        elif mode == 'custom':
            self.lbl_hint.text = "定额模式: 自动调整画质/尺寸，使文件小于目标值(KB)"
            self.input_size.height = '45dp'
            self.input_size.opacity = 1

    def log(self, msg, level="INFO"):
        color = "666666"
        if level == "ERROR": color = "ff4444"
        elif level == "SUCCESS": color = "00aa44"
        time_str = datetime.now().strftime("%H:%M:%S")
        new_line = f"[color=#{color}]>> [{time_str}] {str(msg)}[/color]\n"
        self.console.text = new_line + self.console.text

    # --- 核心压缩算法 (移植自 iTool.py) ---
    def compress_single(self, file_path, save_dir, mode_config):
        try:
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)
            
            with Image.open(file_path) as img:
                img = ImageOps.exif_transpose(img) # 修复旋转
                
                # 1. 定额模式 (如 500KB)
                if mode_config['mode'] == 'target_size':
                    target_bytes = mode_config['kb'] * 1024
                    # 尝试直接保存
                    buf = io.BytesIO()
                    img.save(buf, format=img.format if img.format else 'JPEG', quality=95)
                    if buf.tell() <= target_bytes:
                         # 已经达标，直接复制
                        final_img = img
                        save_kwargs = {'quality': 95}
                        save_kwargs['format'] = img.format if img.format else 'JPEG'
                    else:
                        # 循环逼近
                        final_img, save_kwargs = self._algorithm_target_size(img, target_bytes)
                    
                    out_name = filename
                
                # 2. 预设模式
                else:
                    final_img = img
                    # 调整尺寸
                    limit_w = mode_config.get('width')
                    if limit_w:
                        w, h = final_img.size
                        if w > limit_w:
                            ratio = limit_w / w
                            final_img = final_img.resize((limit_w, int(h*ratio)), Image.Resampling.LANCZOS)
                    
                    save_kwargs = {'quality': mode_config['q'], 'optimize': True}
                    
                    # 格式处理
                    if mode_config.get('format') == 'WEBP':
                        out_name = f"{name}.webp"
                        save_kwargs['format'] = 'WEBP'
                    else:
                        out_name = filename
                        # 修正RGBA转JPG变黑问题
                        if ext.lower() in ['.jpg', '.jpeg'] and final_img.mode == 'RGBA':
                             # 创建白底背景
                             bg = Image.new("RGB", final_img.size, (255, 255, 255))
                             bg.paste(final_img, mask=final_img.split()[3]) 
                             final_img = bg
                        save_kwargs['format'] = 'JPEG' if ext.lower() in ['.jpg', '.jpeg'] else final_img.format

                # 保存到 Download/iTool_Images
                out_path = os.path.join(save_dir, out_name)
                # 防止重名覆盖
                if os.path.exists(out_path):
                    timestamp = int(time.time())
                    out_path = os.path.join(save_dir, f"{name}_{timestamp}{os.path.splitext(out_name)[1]}")

                final_img.save(out_path, **save_kwargs)
                return True, os.path.getsize(out_path)

        except Exception as e:
            self.log(f"处理失败 {filename}: {e}", "ERROR")
            return False, 0

    def _algorithm_target_size(self, img, target_bytes):
        """逼近算法"""
        fmt = 'JPEG'
        if img.mode == 'RGBA': img = img.convert('RGB')
        
        # 阶段1: 降质
        min_q = 30
        for q in range(90, min_q, -5):
            buf = io.BytesIO()
            img.save(buf, format=fmt, quality=q)
            if buf.tell() <= target_bytes:
                return img, {'quality': q, 'format': fmt, 'optimize': True}
        
        # 阶段2: 缩图
        curr_w, curr_h = img.size
        while True:
            curr_w = int(curr_w * 0.9)
            curr_h = int(curr_h * 0.9)
            if curr_w < 200: break
            
            resized = img.resize((curr_w, curr_h), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            resized.save(buf, format=fmt, quality=min_q)
            if buf.tell() <= target_bytes:
                return resized, {'quality': min_q, 'format': fmt, 'optimize': True}
        
        return img, {'quality': min_q, 'format': fmt} # 尽力了

    # --- 流程控制 ---
    def start_processing(self, instance):
        if not self.selected_files:
            self.log("请先选择图片！", "ERROR")
            return
        
        # 获取配置
        config = {}
        if self.opt_balance.state == 'down':
            config = {'mode': 'preset', 'q': 80, 'width': 1920, 'format': 'ORIGINAL'}
        elif self.opt_extreme.state == 'down':
            config = {'mode': 'preset', 'q': 75, 'width': 1280, 'format': 'WEBP'}
        elif self.opt_custom.state == 'down':
            txt = self.input_size.text.strip()
            if not txt or not txt.isdigit():
                self.log("请输入有效的目标大小(KB)", "ERROR")
                return
            config = {'mode': 'target_size', 'kb': int(txt)}

        self.prog.opacity = 1
        self.prog.value = 0
        self.btn_run.disabled = True
        self.log("正在初始化引擎...", "INFO")
        
        # 异步执行防止卡顿
        Clock.schedule_once(lambda dt: self._process_thread(config), 0.1)

    def _process_thread(self, config):
        # 确定输出目录
        out_dir = "/storage/emulated/0/Download/iTool_Images"
        if not os.path.exists(out_dir):
            try:
                os.makedirs(out_dir)
            except:
                self.log("无法创建目录，尝试使用 cache", "WARN")
                out_dir = self.user_data_dir # 降级方案

        success_count = 0
        total = len(self.selected_files)
        
        for i, path in enumerate(self.selected_files):
            # 更新UI
            self.prog.value = (i / total) * 100
            
            ok, size = self.compress_single(path, out_dir, config)
            if ok: success_count += 1
        
        self.prog.value = 100
        self.log(f"完成！成功 {success_count}/{total} 张", "SUCCESS")
        self.log(f"图片已保存至: Download/iTool_Images", "SUCCESS")
        self.btn_run.disabled = False
        Clock.schedule_once(lambda dt: setattr(self.prog, 'opacity', 0), 4)

    # --- 安卓交互 (JNI) ---
    def bind_android(self, dt):
        try:
            from android import activity
            activity.bind(on_activity_result=self.on_android_result)
        except:
            pass

    def open_picker(self, *args):
        if platform == 'android':
            try:
                from jnius import autoclass, cast
                Intent = autoclass('android.content.Intent')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
                
                intent = Intent()
                intent.setAction(Intent.ACTION_GET_CONTENT)
                intent.setType("image/*") # 只选图片
                intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, True) # 允许开启多选
                
                currentActivity.startActivityForResult(intent, 102) # 请求码 102
            except Exception as e:
                self.log(f"JNI 错误: {e}", "ERROR")
        else:
            self.log("非安卓环境，无法调用系统相册", "WARN")
            # 调试用：模拟选择
            # self.selected_files = ['test.jpg']

    def on_android_result(self, requestCode, resultCode, intent):
        if requestCode == 102 and resultCode == -1 and intent:
            self.log("正在解析文件...", "INFO")
            # 开启线程处理文件复制，避免UI卡死
            Clock.schedule_once(lambda dt: self._parse_intent(intent), 0.1)

    def _parse_intent(self, intent):
        try:
            from jnius import autoclass, cast
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            act = cast('android.app.Activity', PythonActivity.mActivity)
            resolver = act.getContentResolver()
            
            uris = []
            
            # 1. 检查 ClipData (多选)
            clip_data = intent.getClipData()
            if clip_data:
                count = clip_data.getItemCount()
                for i in range(count):
                    uris.append(clip_data.getItemAt(i).getUri())
            # 2. 检查 Data (单选)
            elif intent.getData():
                uris.append(intent.getData())
            
            self.selected_files = []
            cache_dir = act.getCacheDir().getAbsolutePath()
            
            for i, uri in enumerate(uris):
                # 复制到 Cache
                inp = resolver.openInputStream(uri)
                # 生成临时文件名
                fname = f"temp_img_{i}_{int(time.time())}.jpg" # 简单处理，不管后缀
                out_path = os.path.join(cache_dir, fname)
                
                FileOutputStream = autoclass('java.io.FileOutputStream')
                out = FileOutputStream(out_path)
                
                buf = bytearray(65536)
                while True:
                    n = inp.read(buf)
                    if n <= 0: break
                    out.write(buf[:n])
                
                inp.close()
                out.close()
                self.selected_files.append(out_path)

            self.status_label.text = f"已就绪: {len(self.selected_files)} 张图片"
            self.status_label.color = (0.2, 0.7, 0.2, 1)
            self.log(f"成功导入 {len(self.selected_files)} 张图片", "SUCCESS")

        except Exception as e:
            self.log(f"文件导入失败: {e}", "ERROR")
            traceback.print_exc()

if __name__ == '__main__':
    try:
        ImageCompressorApp().run()
    except Exception as e:
        # 简易崩溃捕获
        from kivy.base import runTouchApp
        from kivy.uix.label import Label
        runTouchApp(Label(text=str(e), color=(1,0,0,1)))

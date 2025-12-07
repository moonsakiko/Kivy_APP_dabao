import os
import glob
import re
import traceback
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.utils import platform
from kivy.clock import Clock

# 尝试导入 pypdf，如果失败（比如没打包进去）也不会直接闪退，而是会在界面报错
try:
    from pypdf import PdfReader, PdfWriter
    PYPDF_AVAILABLE = True
except ImportError as e:
    PYPDF_AVAILABLE = False
    PYPDF_ERROR = str(e)

class PDFToolApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 1. 状态/日志显示区 (用 ScrollView 包裹防止文字溢出)
        self.log_scroll = ScrollView(size_hint=(1, 0.4))
        self.log_label = Label(text="正在初始化...\n请点击'请求权限'按钮开始", 
                               size_hint_y=None, markup=True)
        self.log_label.bind(texture_size=self.log_label.setter('size'))
        self.log_scroll.add_widget(self.log_label)
        self.layout.add_widget(self.log_scroll)

        # 2. 输入区 (页码范围)
        self.input_range = TextInput(hint_text="输入提取范围 (如: 1-5, 8)", 
                                     size_hint=(1, 0.1), multiline=False)
        self.layout.add_widget(self.input_range)

        # 3. 操作按钮区
        btn_layout = BoxLayout(size_hint=(1, 0.15), spacing=10)
        
        self.btn_scan = Button(text="1. 扫描/刷新文件", on_press=self.scan_files)
        self.btn_extract = Button(text="2. 提取PDF", on_press=self.extract_action)
        
        btn_layout.add_widget(self.btn_scan)
        btn_layout.add_widget(self.btn_extract)
        self.layout.add_widget(btn_layout)

        # 4. 权限按钮 (Android 必需)
        if platform == 'android':
            btn_perm = Button(text="请求存储权限", size_hint=(1, 0.1), 
                              on_press=self.request_android_permissions)
            self.layout.add_widget(btn_perm)

        self.current_files = []
        return self.layout

    def log(self, msg):
        """将日志输出到屏幕 Label，而不是控制台"""
        self.log_label.text += f"\n{msg}"
        # 自动滚动到底部
        Clock.schedule_once(lambda dt: self.log_scroll.scroll_to(self.log_label))

    def request_android_permissions(self, instance):
        """请求 Android 读写权限"""
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.READ_EXTERNAL_STORAGE, 
                                 Permission.WRITE_EXTERNAL_STORAGE])
            self.log("[INFO] 已发送权限请求，请允许。")
        except Exception as e:
            self.log(f"[WARN] 权限请求失败 (非Android环境?): {e}")

    def scan_files(self, instance):
        """扫描 Download 目录下的 PDF"""
        try:
            # Android 默认路径通常在 /sdcard/Download
            # 为了兼容 Termux 和打包环境，尝试多个路径
            search_paths = [
                "/sdcard/Download",
                "/storage/emulated/0/Download",
                ".", # 当前目录
            ]
            
            found_pdfs = []
            for path in search_paths:
                if os.path.exists(path):
                    pdfs = glob.glob(os.path.join(path, "*.pdf"))
                    found_pdfs.extend(pdfs)
            
            # 去重
            self.current_files = sorted(list(set(found_pdfs)))
            
            if not self.current_files:
                self.log("[INFO] 未找到 PDF 文件 (请确保文件在 Download 文件夹)")
            else:
                self.log(f"[SUCCESS] 找到 {len(self.current_files)} 个 PDF:")
                for f in self.current_files:
                    self.log(f" - {os.path.basename(f)}")
                    
        except Exception as e:
            self.log(f"[ERROR] 扫描失败: {e}")

    def extract_action(self, instance):
        """执行提取逻辑"""
        if not PYPDF_AVAILABLE:
            self.log(f"[FATAL] 缺少 pypdf 库! Error: {PYPDF_ERROR}")
            return

        if not self.current_files:
            self.log("[ERROR] 请先扫描文件")
            return
            
        # 为了极简，默认处理第一个找到的文件，或者你可以添加逻辑选择
        target_file = self.current_files[0] 
        range_str = self.input_range.text.strip()
        
        if not range_str:
            self.log("[ERROR] 请输入页码范围 (如 1-3)")
            return

        self.log(f"正在处理: {os.path.basename(target_file)}...")
        
        # 放在线程或用 try-catch 包裹防止崩坏
        try:
            self.do_extraction(target_file, range_str)
        except Exception as e:
            self.log(f"[CRASH] 处理出错:\n{traceback.format_exc()}")

    def do_extraction(self, filepath, range_str):
        # 这里复用你之前的逻辑，但要把 print 换成 self.log
        reader = PdfReader(filepath)
        total_pages = len(reader.pages)
        
        # 简单的页码解析逻辑
        pages = []
        try:
            parts = range_str.replace(' ', '').split(',')
            for part in parts:
                if '-' in part:
                    s, e = part.split('-')
                    e = total_pages if e.lower() == 'end' else int(e)
                    pages.extend(range(int(s)-1, e))
                else:
                    pages.append(int(part)-1)
        except ValueError:
            self.log("[ERROR] 页码格式错误")
            return

        writer = PdfWriter()
        writer.append(fileobj=filepath, pages=pages)
        
        out_name = filepath.replace(".pdf", f"_extracted.pdf")
        with open(out_name, "wb") as f:
            writer.write(f)
            
        self.log(f"[Done] 成功导出:\n{out_name}")

if __name__ == '__main__':
    PDFToolApp().run()

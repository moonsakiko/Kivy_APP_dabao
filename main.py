import os
import traceback
from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.utils import platform

# 1. 强行注册中文字体 (解决方框乱码的核心)
# 只要你上传了 font.ttf，这里就会生效
try:
    LabelBase.register(name="Roboto", fn_regular="font.ttf")
    LabelBase.register(name="Roboto-Bold", fn_regular="font.ttf")
except:
    pass # 防止电脑端测试如果没有字体报错

from kivymd.app import MDApp
from kivymd.uix.filemanager import MDFileManager
from kivymd.toast import toast
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton

# 界面布局 (Material Design 风格)
KV = '''
MDBoxLayout:
    orientation: 'vertical'

    MDTopAppBar:
        title: "PDF 工具箱"
        elevation: 2
        md_bg_color: .2, .2, .2, 1
        specific_text_color: 1, 1, 1, 1

    MDBoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(20)

        # 状态卡片
        MDCard:
            size_hint_y: None
            height: dp(60)
            radius: [10,]
            md_bg_color: .9, .9, .9, 1
            padding: dp(10)
            
            MDLabel:
                id: status_label
                text: "准备就绪 (KivyMD 版)"
                halign: "center"
                theme_text_color: "Primary"
                font_style: "Subtitle1"

        # 功能区
        MDTextField:
            id: field_path
            hint_text: "当前文件路径"
            helper_text: "请点击下方按钮选择文件"
            helper_text_mode: "persistent"
            readonly: True
            multiline: False

        MDRaisedButton:
            text: "📂 选择 PDF 文件"
            pos_hint: {"center_x": .5}
            md_bg_color: 0, 0.4, 0.8, 1
            size_hint_x: 0.8
            on_release: app.file_manager_open()

        MDTextField:
            id: field_range
            hint_text: "输入页码 (例如: 1-5, 8)"
            helper_text: "支持逗号和连字符"
            helper_text_mode: "on_focus"

        MDRaisedButton:
            text: "🚀 开始提取"
            pos_hint: {"center_x": .5}
            md_bg_color: 0, 0.6, 0.2, 1
            size_hint_x: 0.8
            on_release: app.do_extract()

        Widget: # 占位符，把内容顶上去
'''

class PDFToolApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            preview=False, # 关闭预览防止卡顿
        )
        return Builder.load_string(KV)

    def on_start(self):
        if platform == 'android':
            Clock.schedule_once(self.request_perms, 1)

    def log(self, text):
        self.root.ids.status_label.text = text

    def request_perms(self, *args):
        try:
            from android.permissions import request_permissions
            request_permissions([
                "android.permission.READ_EXTERNAL_STORAGE",
                "android.permission.WRITE_EXTERNAL_STORAGE"
            ])
        except:
            pass

    # --- 文件管理器 ---
    def file_manager_open(self):
        # 优先打开 Download 目录
        path = "/storage/emulated/0/Download" if platform == 'android' else os.path.expanduser("~")
        if not os.path.exists(path):
            path = "/storage/emulated/0"
        self.file_manager.show(path)

    def select_path(self, path):
        self.exit_manager()
        if path.endswith(".pdf"):
            self.root.ids.field_path.text = path
            self.log(f"已选中: {os.path.basename(path)}")
            toast(f"选中: {os.path.basename(path)}")
        else:
            toast("请选择 PDF 文件")

    def exit_manager(self, *args):
        self.file_manager.close()

    # --- 提取逻辑 ---
    def do_extract(self):
        try:
            # 懒加载
            from pypdf import PdfReader, PdfWriter
        except ImportError:
            self.log("错误: 缺少 pypdf 库")
            return

        path = self.root.ids.field_path.text
        if not path or not os.path.exists(path):
            toast("请先选择有效文件")
            return

        page_str = self.root.ids.field_range.text
        if not page_str:
            toast("请输入页码")
            return

        try:
            reader = PdfReader(path)
            writer = PdfWriter()
            
            # 简单的页码解析
            indices = []
            for part in page_str.replace(' ', '').split(','):
                if '-' in part:
                    s, e = part.split('-')
                    indices.extend(range(int(s)-1, len(reader.pages) if e=='end' else int(e)))
                else:
                    indices.append(int(part)-1)

            writer.append(fileobj=path, pages=indices)
            
            # 保存到 Download
            save_dir = "/storage/emulated/0/Download" if platform == 'android' else "."
            out_name = f"提取_{os.path.basename(path)}"
            out_path = os.path.join(save_dir, out_name)
            
            with open(out_path, "wb") as f:
                writer.write(f)
            
            self.log("✅ 成功！已保存至 Download")
            self.show_success_dialog(out_path)
            
        except Exception as e:
            self.log(f"❌ 失败: {str(e)}")
            toast(f"出错: {str(e)}")

    def show_success_dialog(self, path):
        dialog = MDDialog(
            title="处理完成",
            text=f"文件已保存:\n{path}",
            buttons=[MDFlatButton(text="好的", on_release=lambda x: dialog.dismiss())]
        )
        dialog.open()

if __name__ == '__main__':
    try:
        PDFToolApp().run()
    except Exception as e:
        print(e)

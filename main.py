import sys
import os
import base64
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding

THEMES = {
    "light": {
        "main_bg": "#f5f5f7", "side_bg": "#ebebeb", "card_bg": "#ffffff",
        "text": "#1d1d1f", "sub_text": "#777", "border": "#dcdcdc",
        "accent": "#0071e3"
    },
    "dark": {
        "main_bg": "#121212", "side_bg": "#181818", "card_bg": "#1e1e1e",
        "text": "#e0e0e0", "sub_text": "#888", "border": "#333333",
        "accent": "#3a8bff"
    }
}

class NotificationBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(260, 28)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout = QHBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0)
        self.bg_frame = QFrame(); self.bg_frame.setObjectName("container")
        layout.addWidget(self.bg_frame)
        self.msg_lbl = QLabel()
        self.msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        QHBoxLayout(self.bg_frame).addWidget(self.msg_lbl)
        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.anim = QPropertyAnimation(self.effect, b"opacity")
        self.hide()

    def show_msg(self, message, is_error=False):
        bg = "rgba(230, 255, 230, 0.95)" if not is_error else "rgba(255, 230, 230, 0.95)"
        text_color = "#008000" if not is_error else "#b30000"
        self.bg_frame.setStyleSheet(f"#container {{ background-color: {bg}; border-radius: 3px; }}")
        self.msg_lbl.setStyleSheet(f"color: {text_color}; font-size: 11px; font-weight: 500;")
        self.msg_lbl.setText(message)
        x = (self.parent().width() - self.width()) // 2
        self.move(x, 15)
        self.anim.setDuration(500)
        self.anim.setStartValue(0); self.anim.setEndValue(1)
        self.show(); self.anim.start()
        QTimer.singleShot(3000, self.fade_out)

    def fade_out(self):
        self.anim.setStartValue(1); self.anim.setEndValue(0)
        self.anim.finished.connect(self.hide)
        self.anim.start()

class ElegantUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_theme = "light"
        self.pub_edit = QLineEdit()
        self.priv_edit = QLineEdit()
        self.setFixedSize(640, 480)
        self.init_ui()
        self.apply_theme()
        self.notifier = NotificationBar(self)

    def init_ui(self):
        main = QWidget(); self.setCentralWidget(main)
        self.layout = QHBoxLayout(main); self.layout.setContentsMargins(0, 0, 0, 0); self.layout.setSpacing(0)
        side = QWidget(); side.setFixedWidth(140)
        side_lay = QVBoxLayout(side); side_lay.setContentsMargins(10, 20, 10, 20)
        self.menu = QListWidget(); self.menu.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.menu.addItems(["数据解密", "数据加密", "生成密钥", "配置管理"])
        self.menu.currentRowChanged.connect(lambda i: self.stack.setCurrentIndex(i))
        self.theme_btn = QToolButton(); self.theme_btn.setText("◑"); self.theme_btn.setStyleSheet("border: none; font-size: 18px; color: #888;")
        self.theme_btn.clicked.connect(self.toggle_theme)
        side_lay.addWidget(self.menu); side_lay.addStretch(); side_lay.addWidget(self.theme_btn)
        self.stack = QStackedWidget()
        for p in [self.create_io_page("解密"), self.create_io_page("加密"), self.create_gen_page(), self.create_conf_page()]: self.stack.addWidget(p)
        self.layout.addWidget(side); self.layout.addWidget(self.stack)
        self.menu.setCurrentRow(0)

    def apply_theme(self):
        t = THEMES[self.current_theme]
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {t['main_bg']}; }}
            QLabel {{ color: {t['text']}; }}
            QListWidget {{ background: transparent; border: none; outline: none; }}
            QListWidget::item {{ padding: 8px; color: {t['sub_text']}; border-radius: 3px; }}
            QListWidget::item:selected {{ background-color: {t['card_bg']}; color: {t['accent']}; }}
            QTextEdit, QLineEdit {{ background: {t['card_bg']}; border: 1px solid {t['border']}; color: {t['text']}; border-radius: 3px; padding: 8px; outline: none; }}
            QPushButton {{ background: {t['accent']}; color: white; border-radius: 3px; padding: 6px; border: none; outline: none; }}
            #copyBtn {{ background: transparent; color: {t['sub_text']}; border: 1px solid {t['border']}; }}
            QScrollBar:vertical {{ border: none; background: transparent; width: 8px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background: {t['border']}; min-height: 20px; border-radius: 4px; }}
            QScrollBar::handle:vertical:hover {{ background: {t['sub_text']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
        """)

    def toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme()

    def select_file(self, line_edit):
        f, _ = QFileDialog.getOpenFileName(self, "选择文件")
        if f: line_edit.setText(f)

    def generate_keys(self):
        folder = QFileDialog.getExistingDirectory(self, "保存位置")
        if not folder: return
        try:
            priv = rsa.generate_private_key(65537, 2048)
            priv_p = os.path.join(folder, "private_key.pem")
            pub_p = os.path.join(folder, "public_key.pem")
            with open(priv_p, "wb") as f: f.write(priv.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
            with open(pub_p, "wb") as f: f.write(priv.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
            self.pub_edit.setText(pub_p); self.priv_edit.setText(priv_p)
            self.notifier.show_msg("生成成功并已同步", False)
        except Exception as e: self.notifier.show_msg(str(e), True)

    def run_crypto(self, mode, in_f, out_f):
        try:
            txt = in_f.toPlainText().encode(); pad = asym_padding.OAEP(asym_padding.MGF1(hashes.SHA256()), hashes.SHA256(), None)
            if mode == "加密":
                with open(self.pub_edit.text(), "rb") as f: key = serialization.load_pem_public_key(f.read())
                out_f.setText(base64.b64encode(b"".join([key.encrypt(txt[i:i+190], pad) for i in range(0, len(txt), 190)])).decode())
            else:
                with open(self.priv_edit.text(), "rb") as f: key = serialization.load_pem_private_key(f.read(), None)
                data = base64.b64decode(in_f.toPlainText().strip())
                out_f.setText(b"".join([key.decrypt(data[i:i+256], pad) for i in range(0, len(data), 256)]).decode())
            self.notifier.show_msg("处理成功", False)
        except Exception: self.notifier.show_msg("路径有误或数据损坏", True)

    def copy_text(self, txt):
        if txt: QApplication.clipboard().setText(txt); self.notifier.show_msg("已复制", False)

    def create_gen_page(self):
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(40, 30, 40, 30); l.setSpacing(10)
        btn = QPushButton("生成 RSA 密钥对"); btn.clicked.connect(self.generate_keys)
        l.addWidget(QLabel("密钥管理")); l.addWidget(btn); l.addStretch()
        return w

    def create_io_page(self, mode):
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(40, 30, 40, 30); l.setSpacing(8)
        in_f = QTextEdit(); out_f = QTextEdit(); out_f.setReadOnly(True)
        btn = QPushButton(f"开始{mode}"); copy = QPushButton("复制", objectName="copyBtn")
        btn.clicked.connect(lambda: self.run_crypto(mode, in_f, out_f))
        copy.clicked.connect(lambda: self.copy_text(out_f.toPlainText()))
        l.addWidget(QLabel(f"数据{mode}")); l.addWidget(in_f); l.addWidget(btn); l.addWidget(QLabel("结果")); l.addWidget(out_f); l.addWidget(copy); l.addStretch()
        return w

    def create_conf_page(self):
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(40, 30, 40, 30); l.setSpacing(10)
        self.pub_edit.setText("public_key.pem"); self.priv_edit.setText("private_key.pem")
        btn_pub = QPushButton("浏览..."); btn_pub.clicked.connect(lambda: self.select_file(self.pub_edit))
        btn_priv = QPushButton("浏览..."); btn_priv.clicked.connect(lambda: self.select_file(self.priv_edit))
        l.addWidget(QLabel("公钥路径")); l.addWidget(self.pub_edit); l.addWidget(btn_pub)
        l.addWidget(QLabel("私钥路径")); l.addWidget(self.priv_edit); l.addWidget(btn_priv); l.addStretch()
        return w

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 9))
    win = ElegantUI()
    win.show()
    sys.exit(app.exec())
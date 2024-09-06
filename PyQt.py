import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineCore import QWebEngineCookieStore
import requests


class BrowserApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.AuthToken = None
        self.setWindowTitle("小雅下载器")
        self.setGeometry(100, 100, 1500, 800)  # 设置窗口大小为1500x800

        # 创建浏览器视图，设置默认URL
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("https://ccnu.ai-augmented.com/home"))

        # 创建下方侧面板
        self.bottom_panel = QWidget()
        self.bottom_panel.setFixedHeight(100)
        self.bottom_panel_layout = QVBoxLayout()
        self.bottom_panel.setLayout(self.bottom_panel_layout)

        # 布局管理，上下布局
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.browser)
        self.layout.addWidget(self.bottom_panel)

        # 设置中央小部件
        central_widget = QWidget()
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)

        # 一直监听cookies
        self.setup_cookie_store()

        # 监听URL变化
        self.Url = self.browser.url().toString()
        self.browser.urlChanged.connect(self.handle_url_changed)

        # session
        self.session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        self.session.headers.update(headers)


    def setup_cookie_store(self):
        """设置cookie store以监听新添加的cookies。"""
        cookie_store = self.browser.page().profile().cookieStore()
        # 监听 cookieAdded 信号，捕获每个新的cookie
        cookie_store.cookieAdded.connect(self.handle_cookie_added)

    def handle_cookie_added(self, cookie):
        """处理新添加的cookie并检查是否为目标的AuthToken cookie。"""
        cookie_name = cookie.name().data().decode('utf-8')
        if cookie_name == "HS-prd-access-token":
            self.AuthToken = "Bearer " + cookie.value().data().decode('utf-8')
            self.session.headers.update({"Authorization": self.AuthToken})
            print(f"获取到AuthToken: {self.AuthToken}")
        else:
            print(f"Cookie added: {cookie_name} : {cookie.value().data().decode('utf-8')}")

    def handle_url_changed(self, url):
        """处理URL变化事件。"""
        self.Url = url.toString()
        print(f"URL changed: {self.Url}")
        if self.Url == "https://ccnu.ai-augmented.com/app/jx-web/mycourse":
            url = "https://ccnu.ai-augmented.com/api/jx-iresource/group/student/groups?time_flag=1"
            data = self.session.get(url).json().get("data")
            print([i.get("name") for i in data], [i.get("id") for i in data])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BrowserApp()
    window.show()
    sys.exit(app.exec())

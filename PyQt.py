import base64
import os.path
import re
import sys
import json
import time

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QHBoxLayout, QPushButton, \
    QFileDialog, QCheckBox, QSizePolicy, QLineEdit
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl
import requests


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.AuthToken = None
        self.get_course_list = True
        self.setWindowTitle("小雅下载器")
        # 设置窗口大小全屏
        # 首先获取显示器大小
        screen = app.primaryScreen()
        screen_size = screen.size()


        # 创建浏览器视图，设置默认URL
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("https://ccnu.ai-augmented.com/home"))

        # 下载单文件按钮
        self.download_button = QPushButton("下载当前文件")
        self.download_button.setFixedWidth(150)
        self.download_button.clicked.connect(self.download_file)
        self.download_button.setDisabled(True)

        # 下载全部文件按钮
        self.download_all_button = QPushButton("下载当前课程全部文件")
        self.download_all_button.setFixedWidth(150)
        self.download_all_button.clicked.connect(self.download_all_files)
        self.download_all_button.setDisabled(True)

        # 创建下方侧面板
        self.bottom_panel = QWidget()
        self.bottom_panel.setFixedHeight(50)
        self.bottom_panel_layout = QHBoxLayout()
        self.bottom_panel_layout.addWidget(self.download_button)
        self.bottom_panel_layout.addWidget(self.download_all_button)
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

        # 保存下载设置窗口
        self.download_setting_window = DownloadSetting()

        # 账号设置窗口
        self.account_setting_window = AccountSetting()

        # 关于作者窗口
        self.about_author_window = AboutAuthor()

        # 创建会话
        self.session = Session()

        # 创建菜单栏
        self.create_menu()

        self.account = base64.b64decode(json.load(open("account.json")).get("account")).decode() if os.path.exists("account.json") else None
        self.password = base64.b64decode(json.load(open("account.json")).get("password")).decode() if os.path.exists("account.json") else None

        # self.course_list = []

    def create_menu(self):
        menubar = self.menuBar()

        # 创建操作菜单
        action_menu = menubar.addMenu("操作")

        # 添加回退动作
        back_action = QAction("回退", self)
        action_menu.addAction(back_action)
        back_action.triggered.connect(self.browser.back)

        # 添加前进动作
        forward_action = QAction("前进", self)
        action_menu.addAction(forward_action)
        forward_action.triggered.connect(self.browser.forward)

        # 添加刷新动作
        reload_action = QAction("刷新", self)
        action_menu.addAction(reload_action)
        reload_action.triggered.connect(self.browser.reload)

        # 添加退出动作
        exit_action = QAction("退出", self)
        action_menu.addAction(exit_action)
        exit_action.triggered.connect(self.close)

        # 创建设置菜单
        setting_menu = menubar.addMenu("设置")

        # 创建下载设置
        download_setting = QAction("下载设置", self)
        setting_menu.addAction(download_setting)
        download_setting.triggered.connect(self.download_setting_window.show)

        # 创建账号设置
        account_setting = QAction("账号设置", self)
        setting_menu.addAction(account_setting)
        account_setting.triggered.connect(self.account_setting_window.show)

        # 创建帮助菜单
        help_menu = menubar.addMenu("关于")

        # 创建关于作者
        about_author = QAction("关于作者", self)
        help_menu.addAction(about_author)
        about_author.triggered.connect(self.about_author_window.show)


    def setup_cookie_store(self):
        """设置cookie store以监听新添加的cookies。"""
        cookie_store = self.browser.page().profile().cookieStore()
        # 监听 cookieAdded 信号，捕获每个新的cookie
        cookie_store.cookieAdded.connect(self.handle_cookie_added)

    def handle_cookie_added(self, cookie):
        """处理新添加的cookie并检查是否为目标的AuthToken cookie。"""
        cookie_name = cookie.name().data().decode('utf-8')
        self.session.cookies.set(cookie_name, cookie.value().data().decode('utf-8'))
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
        if "https://account.ccnu.edu.cn/" in self.Url:
            time.sleep(1)
            self.browser.page().runJavaScript(f"document.getElementById('username').value = '{self.account}';")
            self.browser.page().runJavaScript(f"document.getElementById('password').value = '{self.password}';")
            self.browser.page().runJavaScript("document.querySelector('#fm1 > section.row.btn-row > input.btn-submit').click();")
        if "https://ccnu.ai-augmented.com/app/jx-web/mycourse" in self.Url:
            self.download_button.setDisabled(True)
            self.download_all_button.setDisabled(True)
            # if self.get_course_list:
            #     flag1 = self.session.get(url="https://ccnu.ai-augmented.com/api/jx-iresource/group/student/groups?time_flag=1")
            #     flag2 = self.session.get(url="https://ccnu.ai-augmented.com/api/jx-iresource/group/student/groups?time_flag=2")
            #     flag3 = self.session.get(url="https://ccnu.ai-augmented.com/api/jx-iresource/group/student/groups?time_flag=3")
            #     self.course_list = flag1.json().get("data") + flag2.json().get("data") + flag3.json().get("data")
            #     print(self.course_list)
            #     self.get_course_list = False
        if re.match(r"https://ccnu.ai-augmented.com/app/jx-web/mycourse/\d+/resource", self.Url):
            self.download_all_button.setDisabled(False)
        if re.match(r"https://ccnu.ai-augmented.com/app/jx-web/mycourse/\d+/resource/\d+/\d+", self.Url):
            self.download_button.setDisabled(False)

    def download_file(self):
        download_path = self.download_setting_window.layout().itemAt(0).itemAt(1).widget().text()
        course_id = re.match(r".*?mycourse/(.*)?/resource.*", self.Url).group(1)
        file_id = re.match(r".*?mycourse/.*?/resource/\d+/(\d+)", self.Url).group(1)
        url = "https://ccnu.ai-augmented.com/api/jx-iresource/resource/queryCourseResources?group_id=" + course_id
        file_list = self.session.get(url=url).json().get("data")
        for file in file_list:
            if file_id == file.get("id"):
                file_name = file.get("name")
                quote_id = file.get("quote_id")
                url = ("https://ccnu.ai-augmented.com/api/jx-oresource/cloud/file_url/" + quote_id)
                download_url = (self.session.get(url=url).json().get("data").get("url"))
                with open(os.path.join(download_path, file_name), "wb") as f:
                    f.write(self.session.get(url=download_url).content)
                break

    def download_all_files(self):
        os.chdir(self.download_setting_window.layout().itemAt(0).itemAt(1).widget().text())
        course_id = re.match(r".*?mycourse/(.*)?/resource.*", self.Url).group(1)
        url = "https://ccnu.ai-augmented.com/api/jx-iresource/resource/queryCourseResources?group_id=" + course_id
        self.make_root(course_id=course_id)
        file_list = self.data2list(self.session.get(url=url).json())
        tree = self.list2tree(file_list=file_list)
        self.makedir_and_download(file_tree=tree)

    def make_root(self, course_id: str):
        name = self.session.post(url="https://ccnu.ai-augmented.com/api/jx-iresource/statistics/group/visit",
                                 data={"group_id": course_id, "role_type": "normal"}).json().get("data").get("name")
        i = 1
        while os.path.exists(name):
            try:
                os.rename(name, f"{name}({i})")
            except:
                i = i + 1
        os.mkdir(name)
        os.chdir(name)

    def data2list(self, data):
        return [
            {"id": i.get("id"), "parent_id": i.get("parent_id"), "mimetype": i.get("mimetype"), "name": i.get("name"),
             "type": i.get("type"), "quote_id": i.get("quote_id"), } for i in data.get("data")]

    def list2tree(self, file_list: list) -> dict:
        mapping: dict = dict(zip([i["id"] for i in file_list], file_list))
        file_tree: dict = {}
        for i in file_list:
            parent: dict = mapping.get(i["parent_id"])
            if parent is None:
                file_tree: dict = i
            else:
                children: file_list = parent.get("children")
                if not children:
                    children: file_list = []
                children.append(i)
                parent.update({"children": children})
        return file_tree

    def makedir_and_download(self, file_tree: dict):
        for i in file_tree.get("children"):
            type: str = i.get("type")
            name: str = i.get("name")
            if type == 1:
                os.mkdir(name)
                os.chdir(name)
                if i.get("children"):
                    self.makedir_and_download(file_tree=i)
                os.chdir("../")
            elif type == 6:
                self.download_wps(item_json=i)
            elif type == 9 and self.download_setting_window.layout().itemAt(1).itemAt(0).widget().isChecked():
                self.download_video(item_json=i)

    def download_wps(self, item_json: dict):
        quote_id: str = item_json.get("quote_id")
        url: str = ("https://ccnu.ai-augmented.com/api/jx-oresource/cloud/file_url/" + quote_id)
        download_url: str = self.session.get(url=url).json().get("data").get("url")
        with open(item_json.get("name"), "wb+") as f:
            f.write(requests.get(url=download_url).content)

    def download_video(self, item_json: dict):
        name: str = item_json.get("name")
        try:
            node_id: str = item_json.get("id")
            get_video_id_url: str = (
                    "https://ccnu.ai-augmented.com/api/jx-iresource/resource/queryResource?node_id=" + node_id)
            video_id = self.session.get(url=get_video_id_url).json().get("data").get("resource").get("video_id")
            get_m3u8_url: str = ("https://ccnu.ai-augmented.com/api/jx-oresource/vod/video/play_auth/" + video_id)
            m3u8_url = self.session.get(url=get_m3u8_url).json().get("data").get("private_vod")[0].get("private_url")
            m3u8_list: str = self.session.get(url=m3u8_url).text
            ts_list: list = re.findall(pattern=".*?\.ts", string=m3u8_list)
            with open(name, "ab+") as f:
                for i in ts_list:
                    url: str = "https://vod-trans-1.ccnu.edu.cn" + i
                    f.write(requests.get(url=url).content)
        except Exception as e:
            print(e)

    def closeEvent(self, event):
        self.browser.close()
        self.download_setting_window.close()
        event.accept()

class Session(requests.Session):
    def __init__(self):
        super().__init__()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        }
        self.headers.update(headers)


class DownloadSetting(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("下载设置")
        # 首先获取显示器大小
        screen = app.primaryScreen()
        screen_size = screen.size()
        # 设置窗口位置
        # self.setGeometry((screen_size.width() - 400) // 2,
        #                  (screen_size.height() - 50) // 2, 400, 50)
        self.setFixedSize(400, 75)

        # 下载路径设置
        download_path_label = QLabel("下载路径")
        download_path = QLabel(os.path.abspath("downloads"))
        if not os.path.exists("downloads"):
            os.mkdir("downloads")
        download_path.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding)
        download_path_set = QPushButton("···")
        download_path_set.setFixedWidth(25)
        download_path_set.clicked.connect(self.set_download_path)

        # 下载路径设置布局
        download_path_layout = QHBoxLayout()
        download_path_layout.addWidget(download_path_label)
        download_path_layout.addWidget(download_path)
        download_path_layout.addWidget(download_path_set)

        # 下载视频设置
        download_video = QCheckBox("下载视频")
        download_video.setChecked(False)
        download_video.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        # 保存下载设置
        download_setting_save = QPushButton("保存")
        download_setting_save.setFixedWidth(50)
        download_setting_save.clicked.connect(self.save_download_setting)

        # 下方按钮布局
        download_setting_button_layout = QHBoxLayout()
        download_setting_button_layout.addWidget(download_video)
        download_setting_button_layout.addWidget(download_setting_save)

        # 下载设置窗口布局
        download_setting_layout = QVBoxLayout()
        download_setting_layout.addLayout(download_path_layout)
        download_setting_layout.addLayout(download_setting_button_layout)

        self.setLayout(download_setting_layout)
        self.get_download_setting()

    def set_download_path(self):
        # 打开文件对话框，选择下载路径
        download_path = QFileDialog.getExistingDirectory(self, "选择下载路径", "")
        if download_path:
            self.layout().itemAt(0).itemAt(1).widget().setText(download_path)

    def save_download_setting(self):
        download_path = self.layout().itemAt(0).itemAt(1).widget().text()
        download_video = self.layout().itemAt(1).itemAt(0).widget().isChecked()
        with open("settings.json", "w+") as f:
            json.dump({"download_path": download_path,
                        "download_video": download_video}, f)
        self.close()

    def get_download_setting(self):
        if os.path.exists("settings.json"):
            with open("settings.json", "r") as f:
                settings = json.load(f)
                self.layout().itemAt(0).itemAt(1).widget().setText(settings.get("download_path"))
                self.layout().itemAt(1).itemAt(0).widget().setChecked(settings.get("download_video"))
        else:
            return None


class AccountSetting(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("账号设置")
        # 首先获取显示器大小
        screen = app.primaryScreen()
        screen_size = screen.size()
        # 设置窗口位置
        # self.setGeometry((screen_size.width() - 300) // 2,
        #                  (screen_size.height() - 100) // 2, 300, 100)
        self.setFixedSize(300, 150)

        # 使用说明
        account_setting_instruction = QLabel("目前仅支持使用统一身份认证自动登录\n请不要把记录你学号密码的文件分享给他人。")

        # 账号设置
        account_setting_label = QLabel("账号")
        account_setting_input = QLineEdit()

        # 密码设置
        password_setting_label = QLabel("密码")
        password_setting_input = QLineEdit()
        password_setting_input.setEchoMode(QLineEdit.EchoMode.Password)

        # 账号设置布局
        account_setting_layout = QHBoxLayout()
        account_setting_layout.addWidget(account_setting_label)
        account_setting_layout.addWidget(account_setting_input)

        # 密码设置布局
        password_setting_layout = QHBoxLayout()
        password_setting_layout.addWidget(password_setting_label)
        password_setting_layout.addWidget(password_setting_input)

        # 保存账号设置
        account_setting_save = QPushButton("保存")
        account_setting_save.setFixedWidth(50)
        account_setting_save.clicked.connect(self.save_account_setting)

        # 设置布局
        setting_layout = QVBoxLayout()
        setting_layout.addWidget(account_setting_instruction)
        setting_layout.addLayout(account_setting_layout)
        setting_layout.addLayout(password_setting_layout)
        setting_layout.addWidget(account_setting_save)

        # 账号设置窗口布局
        self.setLayout(setting_layout)

    def save_account_setting(self):
        # 使用base64加密保存账号密码
        account = base64.b64encode(self.layout().itemAt(1).itemAt(1).widget().text().encode()).decode()
        password = base64.b64encode(self.layout().itemAt(2).itemAt(1).widget().text().encode()).decode()
        with open("account.json", "w+") as f:
            json.dump({"account": account,
                       "password": password}, f)
        self.parent().account = self.layout().itemAt(1).itemAt(1).widget().text()
        self.parent().password = self.layout().itemAt(2).itemAt(1).widget().text()
        self.close()

class AboutAuthor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("关于作者")
        # 首先获取显示器大小
        screen = app.primaryScreen()
        screen_size = screen.size()
        # 设置窗口位置
        # self.setGeometry((screen_size.width() - 300) // 2,
        #                  (screen_size.height() - 100) // 2, 300, 100)
        self.setFixedSize(450, 85)

        # 关于作者
        author_info = QLabel("作者：")
        author_info_link = QLabel('<a href="https://github.com/CN-Grace">Grace</a>')
        author_info_link.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding)
        author_info_link.setOpenExternalLinks(True)

        # 项目地址
        project_address = QLabel("项目地址：")
        project_address_link = QLabel(
            '<a href="https://github.com/zhouxinghua001/Xiaoya-Downloader-PyQt">https://github.com/zhouxinghua001/Xiaoya-Downloader-PyQt</a>')
        project_address_link.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding)
        project_address_link.setOpenExternalLinks(True)

        # 联系方式
        contact_info = QLabel("作者邮箱：")
        contact_info_url = QLabel('<a href="mailto:grace@linuxdo.edu.pl">发送邮件</a>  grace@linuxdo.edu.pl')
        contact_info_url.setOpenExternalLinks(True)

        # 左侧关于作者布局
        Left_layout = QVBoxLayout()
        Left_layout.addWidget(author_info)
        Left_layout.addWidget(project_address)
        Left_layout.addWidget(contact_info)

        # 右侧关于作者布局
        Right_layout = QVBoxLayout()
        Right_layout.addWidget(author_info_link)
        Right_layout.addWidget(project_address_link)
        Right_layout.addWidget(contact_info_url)

        # 关于作者布局
        author_layout = QHBoxLayout()
        author_layout.addLayout(Left_layout)
        author_layout.addLayout(Right_layout)
        self.setLayout(author_layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.showMaximized()
    sys.exit(app.exec())
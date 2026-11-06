"""Native Qt Store window. The backend alone owns filesystem/process actions."""
import sys
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,
    QLabel,QLineEdit,QComboBox,QListWidget,QListWidgetItem,QPushButton,QTextBrowser,
    QMessageBox,QSplitter)
from store_manager import safe_path


class StoreWindow(QMainWindow):
    def __init__(self,store):
        super().__init__();self.store=store;self.key=None
        self.setWindowTitle('OREZ Store');self.resize(1080,760);self.setMinimumSize(760,580)
        root=QWidget();self.setCentralWidget(root);layout=QVBoxLayout(root);layout.setContentsMargins(28,24,28,24);layout.setSpacing(16)
        brand=QLabel('OREZ   /   STORE');brand.setObjectName('brand');layout.addWidget(brand)
        title=QLabel('Find your everyday essentials.');title.setObjectName('title');layout.addWidget(title)
        subtitle=QLabel('Free to use. Clear permissions. Your choice of apps.');layout.addWidget(subtitle)
        filters=QHBoxLayout();self.search=QLineEdit();self.search.setObjectName('store-search');self.search.setAccessibleName('Search apps');self.search.setPlaceholderText('Search apps, publishers or categories…');filters.addWidget(self.search,1)
        self.kind=QComboBox();self.kind.setObjectName('store-kind');self.kind.setAccessibleName('App format');self.kind.addItems(['All apps','Android','Native Linux']);filters.addWidget(self.kind)
        self.library=QPushButton('My apps');self.library.setCheckable(True);self.library.setAccessibleName('Show my apps');filters.addWidget(self.library);layout.addLayout(filters)
        split=QSplitter(Qt.Horizontal);self.items=QListWidget();self.items.setObjectName('store-list');self.items.setAccessibleName('Apps');self.items.setMinimumWidth(265);split.addWidget(self.items)
        details=QWidget();detail=QVBoxLayout(details);detail.setContentsMargins(25,8,4,8);detail.setSpacing(12)
        self.name=QLabel();self.name.setTextFormat(Qt.PlainText);self.name.setObjectName('app-title');self.name.setWordWrap(True);detail.addWidget(self.name)
        self.badge=QLabel();self.badge.setTextFormat(Qt.PlainText);self.badge.setWordWrap(True);detail.addWidget(self.badge)
        self.description=QTextBrowser();self.description.setObjectName('app-details');self.description.setOpenExternalLinks(False);self.description.setAccessibleName('App details and permissions');detail.addWidget(self.description,1)
        buttons=QHBoxLayout();self.primary=QPushButton();self.primary.setObjectName('primary-action');buttons.addWidget(self.primary)
        self.runtime=QPushButton('Android runtime controls');self.runtime.setObjectName('android-runtime');buttons.addWidget(self.runtime);detail.addLayout(buttons)
        options=QHBoxLayout();self.source=QPushButton('Publisher information');self.source.setObjectName('official-source');options.addWidget(self.source)
        detail.addLayout(options)
        split.addWidget(details);split.setSizes([310,670]);layout.addWidget(split,1)
        lower=QHBoxLayout();self.activity=QPushButton('Activity and controls');self.activity.setObjectName('store-activity');lower.addWidget(self.activity);lower.addStretch();note=QLabel('No automatic purchases • No administrator service');lower.addWidget(note);layout.addLayout(lower)
        self.status=QLabel('Browse offline. Nothing is downloaded when you open the store.');self.status.setWordWrap(True);self.status.setObjectName('store-status');layout.addWidget(self.status)
        self.search.textChanged.connect(self.refresh);self.kind.currentIndexChanged.connect(self.refresh);self.library.toggled.connect(self.refresh)
        self.items.currentItemChanged.connect(self.select);self.primary.clicked.connect(self.perform_primary);self.runtime.clicked.connect(self.runtime_controls);self.source.clicked.connect(self.open_source);self.activity.clicked.connect(self.show_activity)
        self.setStyleSheet('''QWidget{background:#f5f3ee;color:#222;font-family:"Noto Sans";font-size:14px}
            QLabel#brand{font-size:12px;font-weight:600;letter-spacing:3px} QLabel#title{font-size:30px;font-weight:500}
            QLabel#app-title{font-size:25px;font-weight:600} QLineEdit,QComboBox{background:#fff;padding:11px;border:1px solid #aaa;border-radius:8px}
            QListWidget{background:#eeece6;border:1px solid #ccc;border-radius:10px;padding:8px} QListWidget::item{padding:15px;border-radius:7px} QListWidget::item:selected{background:#303030;color:white}
            QTextBrowser{background:#fffdf9;border:1px solid #d4d1c9;border-radius:10px;padding:15px}
            QPushButton{background:#fffdf9;padding:10px 14px;border:1px solid #888;border-radius:7px} QPushButton:hover{background:#e5e2db} QPushButton:focus{border:2px solid #111}
            QPushButton:checked,QPushButton#primary-action{background:#292929;color:#fff} QPushButton:disabled{background:#e6e3dc;color:#666;border-color:#ccc}
            QLabel#store-status{color:#444;font-size:12px;padding-top:4px}''')
        self.refresh()

    def refresh(self,*args):
        previous=self.key;query=self.search.text().strip().casefold();kind=['','android','native'][self.kind.currentIndex()]
        self.items.blockSignals(True);self.items.clear()
        for app in self.store.apps.values():
            if kind and app['kind']!=kind:continue
            if query not in ' '.join(app[field] for field in ['name','publisher','category']).casefold():continue
            try:state=self.store.status(app['id'])
            except (OSError,ValueError):state={'installed':False}
            if self.library.isChecked() and not state['installed']:continue
            label={'native':'Native Linux','android':'Android • pending'}[app['kind']]
            item=QListWidgetItem(app['name']+'\n'+label);item.setData(Qt.UserRole,app['id']);self.items.addItem(item)
        self.items.blockSignals(False)
        row=next((i for i in range(self.items.count()) if self.items.item(i).data(Qt.UserRole)==previous),0)
        if self.items.count(): self.items.setCurrentRow(row)
        else:self.select(None)

    def select(self,item,*args):
        self.key=item.data(Qt.UserRole) if item else None
        for button in [self.primary,self.source,self.runtime]:button.setEnabled(bool(item))
        if not item:
            self.name.setText('No matching apps');self.badge.setText('Try another search or app format.');self.description.clear();self.primary.setText('Unavailable');return
        app=self.store.app(self.key)
        try:state=self.store.status(self.key);error=''
        except (OSError,ValueError) as caught:state={'installed':False,'state':'Needs attention','browser_available':False};error=str(caught)
        self.name.setText(app['name']);self.badge.setText(app['publisher']+'  /  '+state['state'])
        cost='Free base download where offered. Optional purchases, subscriptions and regional availability remain publisher-controlled.'
        self.description.setPlainText(app['summary']+'\n\nPRICE\n'+cost+'\n\nCOMPATIBILITY\n'+app['compatibility']+'\n\nACCESS & YOUR DATA\n'+app['privacy']+'\n\nOWNER CONTROL\nNo automatic administrator access. No automatic payments. Other software sources and the terminal remain available.'+('\n\n'+error if error else ''))
        if app['kind']=='native':
            self.primary.setText('Open native app' if state['installed'] else 'Installation information')
            self.primary.setEnabled(not error)
        else:
            self.primary.setText('Android runtime pending');self.primary.setEnabled(False)
        self.runtime.setEnabled(True)

    def ask(self,title,text):
        return QMessageBox.question(self,title,text,QMessageBox.Yes|QMessageBox.Cancel,QMessageBox.Cancel)==QMessageBox.Yes

    def action(self,operation,message):
        try:operation();self.status.setText(message);self.refresh()
        except (OSError,ValueError) as error:
            self.status.setText(str(error));QMessageBox.warning(self,'OREZ Store',str(error))

    def perform_primary(self):
        if not self.key:return
        key=self.key
        try:state=self.store.status(key)
        except (OSError,ValueError) as error:
            self.status.setText(str(error));QMessageBox.warning(self,'OREZ Store',str(error));return
        if self.store.app(key)['kind']=='android':return
        if not state['installed']:self.open_source()
        else:self.action(lambda:self.store.launch(key),'Native launch requested as your ordinary user; compatibility remains a separate check.')

    def runtime_controls(self):
        if self.ask('Open development runtime controls?',
                    'The current Android SDK provider is for permitted development/testing only. It is not a qualified consumer Play Store. Setup displays licence prompts and is never automatic. Open its status, setup, start/stop and memory controls?'):
            self.action(lambda:self.store.runtime_controls(True),'Development runtime controls requested. No app was installed or purchased.')

    def open_source(self):
        key=self.key
        if key and self.ask('Open publisher information?','Open '+self.store.app(key)['url']+' for information only in your default browser? This does not run the app. The site can receive your IP and browser information. OREZ will not download, install or purchase anything automatically.'):
            self.action(lambda:self.store.open_source(key,True),'Official source requested in your browser. Installation was not performed by OREZ Store.')

    def show_activity(self):
        path=self.store.root/'actions.jsonl'
        text=('Official Linux desktop versions are preferred unchanged. YouTube, Instagram and the requested Android games are not web shortcuts.\n'
              'One shared Android runtime is planned, with per-app desktop launchers; consumer integration is unfinished.\n'
              'Direct keyboard/mouse compatibility must be tested per app; no custom key mapping is installed.\n'
              'Android permissions, app updates and app removal belong inside Android. Stop/reset controls are in OREZ Android Apps.\n'
              'No automatic purchases, APK mirrors or administrator service. Other installation routes remain available.\n\n'
              'Local Store logs: '+str(self.store.root)+'\nLaunch logs may contain private application error details.\n\nRecent local actions (no credentials):\n')
        try:
            safe_path(path)
            if path.is_file():text+='\n'.join(path.read_text()[-12000:].splitlines()[-20:])
            else:text+='No actions recorded.'
        except (OSError,ValueError) as error:text+='Unavailable: '+str(error)
        box=QMessageBox(self);box.setWindowTitle('Activity and controls');box.setTextFormat(Qt.PlainText);box.setText(text);box.exec()


def run(store):
    app=QApplication.instance() or QApplication(sys.argv);app.setApplicationName('OREZ Store')
    window=StoreWindow(store);window.show();return app.exec()

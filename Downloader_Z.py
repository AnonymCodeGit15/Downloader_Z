"""Downloader Z
A PyQt6 Based GUI downloader with support for custom chunk sizes,verification of file integrity (md5)
, decryption of 7z downloaded file , extraction of 7z file and many more features such as support for command line
arguments and json file to instantly start download."""
import os.path
import socket
import sys
import time
import json
import py7zr
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
from PySide6.QtCore import Qt, QDate, QPoint, QObject, QThread, Signal, Slot, QTimer, QRect
from PySide6.QtGui import QAction, QPalette, QColor, QIcon, QGuiApplication, QFontDatabase, QFont
from PySide6.QtWidgets import (
    QApplication,
    QSizePolicy,
    QLayout,
    QHBoxLayout,
    QProgressBar,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QMainWindow,
    QStatusBar,
    QMenu,
    QFileDialog,
    QCalendarWidget,
    QWidget, QDialog,
    QMessageBox, QInputDialog, QDialogButtonBox, QFormLayout, QLineEdit
)
import io
from typing import List
import argparse
import hashlib

base_pth = os.getcwd()
app = QApplication(sys.argv)

def my_path(path_name) -> str:
    """Return the appropriate path for data files based on execution context"""
    if getattr(sys, 'frozen', False):
        # running in a bundle (pyinstaller)
        print(os.path.join(sys._MEIPASS, path_name))
        return os.path.join(sys._MEIPASS, path_name)
    else:
        # running live
        return base_pth + "\\" + os.path.basename(path_name)


# Initialize drive service
try :
    credentials = service_account.Credentials.from_service_account_file(my_path("creds.json"))
except Exception as err_CRED:
    # Exit if credentials cannot load
    print("Error finding / loading credentials file.")
    print(f"Error : {str(err_CRED)}")
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setText(f"Error loading credentials file\nError : {str(err_CRED)}")
    msg.setWindowIcon(QIcon(my_path("icon.png")))
    msg.setWindowTitle("Operation Cancelled")
    msg.exec()
    sys.exit(0)


drive_service = build('drive', 'v3', credentials=credentials)
j_loaded = False
# Check if json exists and load configuration json if present
try:
    if os.path.isfile(my_path("config_down.json")):
        with open(my_path("config_down.json"), "r") as file_obj:
            dat_dict = json.load(file_obj)
        file_id = dat_dict["id"]
        file_md5 = dat_dict["md5"]
        file_out_name = dat_dict["file_out"]
        folder_out_name = dat_dict["folder_out"]
        file_pkey = dat_dict["password"]
        data_pending = False
        p_skip = False
        md5_skip = False
        cnt = 0
        for el in (file_id, file_pkey, file_out_name, file_md5, folder_out_name):
            if el != None and el != "":
                cnt += 1
        if cnt == 5:
            data_pending = False
            j_loaded = True
        elif cnt == 4 and (file_md5 == "" or file_md5 == None):
            md5_skip = True
            data_pending = False
            j_loaded = True
        elif cnt == 4 and (file_pkey == "" or file_pkey == None):
            p_skip = True
            data_pending = False
            j_loaded = True
        elif cnt == 3 and (file_pkey == "" or file_pkey == None) and (file_md5 == "" or file_md5 == None):
            p_skip = True
            md5_skip = True
            data_pending = False
            j_loaded = True
        else:
            data_pending = True
            j_loaded = False
        if not j_loaded:
            print("Error loading json file (Incomplete or Incompatible data)")
        else:
            print("Successfully loaded json directly from config_down.json ,Starting now")

except Exception as e:
    print(str(e))
    print("Found json but error loading file.")
# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--id", "-I", type=str, help="Set google drive file id", action="store")
parser.add_argument("--folder_out", "-F", type=str, help="Set output folder name", action="store")
parser.add_argument("--file_out", "-f", type=str, help="Set output zip file name", action="store")
parser.add_argument("--md5", "-C", type=str, help="Set md5 hash to verify the downloaded file with.", action="store")
parser.add_argument("--pkey", "-P", type=str, help="Set password of downloaded file", action="store", default="")
parser.add_argument("--chunk_size", "-S", type=int, help="Set chunk size of downloader", action="store", default=1,
                    choices=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
args = parser.parse_args()
# Check command line arguments to start download if json is not there
if not j_loaded:
    file_id = args.id
    file_md5 = args.md5
    file_out_name = args.file_out
    folder_out_name = args.folder_out
    file_pkey = args.pkey
    data_pending = False
    p_skip = False
    md5_skip = False
    cnt = 0
    for el in (file_id, file_pkey, file_out_name, file_md5, folder_out_name):
        if el != None and el != "":
            cnt += 1
    if cnt == 5:
        data_pending = False
    elif cnt == 4 and (file_md5 == "" or file_md5 == None):
        md5_skip = True
        data_pending = False
    elif cnt == 4 and (file_pkey == "" or file_pkey == None):
        p_skip = True
        data_pending = False
    elif cnt == 3 and (file_pkey == "" or file_pkey == None) and (file_md5 == "" or file_md5 == None):
        p_skip = True
        md5_skip = True
        data_pending = False
    else:
        data_pending = True
cnt = 0



class Data_Input_Dialog(QDialog):
    def __init__(self, labels: List[str], parent=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon(my_path("icon.png")))
        self.setWindowTitle("Input Parameters")
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        layout = QFormLayout(self)

        self.inputs = []
        for lab in labels:
            self.inputs.append(QLineEdit(self))
            layout.addRow(lab, self.inputs[-1])

        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def getInputs(self) -> tuple:
        return tuple(inp.text() for inp in self.inputs)

    def reject(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Operation cancelled")
        msg.setWindowIcon(QIcon(my_path("icon.png")))
        msg.setWindowTitle("Cancelled")
        msg.exec()
        sys.exit(0)

# If neither JSON nor command line arguments given then ask for required data in GUI popup
while data_pending:
    dlg = Data_Input_Dialog(
        labels=["File ID", "File Password (Leave Empty if Unencrypted)", "File Output Name", "Folder Name",
                "File MD5 (Leave "
                "Empty to skip "
                "verification)"])
    ret = dlg.exec()

    file_id, file_pkey, file_out_name, folder_out_name, file_md5 = dlg.getInputs()
    cnt = 0
    for el in (file_id, file_pkey, file_out_name, file_md5, folder_out_name):
        if el != None and el != "":
            cnt += 1
    if cnt == 5:
        data_pending = False
        break
    if cnt == 4 and (file_md5 == "" or file_md5 == None):
        md5_skip = True
        data_pending = False
        break
    if cnt == 4 and (file_pkey == "" or file_pkey == None):
        p_skip = True
        data_pending = False
        break
    if cnt == 3 and (file_pkey == "" or file_pkey == None) and (file_md5 == "" or file_md5 == None):
        p_skip = True
        md5_skip = True
        data_pending = False
        break
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setText("Data Incomplete or Invalid")
    msg.setWindowIcon(QIcon(my_path("icon.png")))
    msg.setWindowTitle("Error")
    msg.exec()

down_chunk_size_mb = args.chunk_size
request = drive_service.files().get_media(fileId=file_id)


class Worker(QObject):
    states = ['Checking connection..', "Starting Download..", "Downloading file ", "Verifying integrity",
              'Extracting files', 'Finalizing', 'Finished']
    finished = Signal()
    progress = Signal(str)
    size = Signal(str)
    error = Signal(str)
    conn = Signal(bool)
    progress_sig = Signal(int)

    @Slot()
    def down(self, id=file_id, out=file_out_name,
             md5=file_md5, folder_name=folder_out_name, passwrd=file_pkey, chunk_size_mb=down_chunk_size_mb):
        try:
            os.chdir(glob_folder)
            print(glob_folder)
            os.mkdir(folder_name)
            os.chdir(folder_name)
            fh = io.FileIO(out, 'wb')  # this can be used to write to disk
            self.progress.emit(self.states[0])
            nstat = self.internet_test()
            self.conn.emit(nstat)
            if not nstat:
                os.chdir("..")
                try:
                    os.rmdir(folder_out_name)
                except Exception:
                    pass
                time.sleep(10)
                sys.exit(0)
            downloader = MediaIoBaseDownload(fh, request, chunksize=1000 ** 2 * chunk_size_mb)
            intel = drive_service.files().get(fileId=id, fields="name,size").execute()

            rounded_size = int(int(intel['size']) / 1000 ** 2)
            self.size.emit(rounded_size)
            self.progress.emit(self.states[1])

            print(str(rounded_size) + ' ' + intel['name'])

            done = False
            dn = 0
            ic = 0
            self.progress.emit(self.states[2])

            while done is False:

                ic += 1

                status, done = downloader.next_chunk()

                if (int(intel['size']) - dn) <= 1000 ** 2 * chunk_size_mb:
                    dn = int(intel['size'])
                else:
                    dn += 1000 ** 2 * chunk_size_mb
                percent = int(status.progress() * 100)
                self.progress_sig.emit(percent)
                print(str(dn / 1000 ** 2) + ' out of ' + str(rounded_size))
                pg = str(dn / 1000 ** 2) + ' / ' + str(rounded_size)

                self.progress.emit(self.states[2] + ' ' + pg)
                print("Download %d%%." % percent)
            if not md5_skip:
                self.progress.emit(self.states[3])
                self.progress_sig.emit(0)
                dn = 0
                with open(out, "rb") as f:
                    file_hash = hashlib.md5()
                    while chunk := f.read(1000 ** 2 * chunk_size_mb):
                        file_hash.update(chunk)
                        if (int(intel['size']) - dn) <= 1000 ** 2 * chunk_size_mb:
                            dn = int(intel['size'])
                            self.progress_sig.emit(100)
                        else:
                            dn += 1000 ** 2 * chunk_size_mb
                            self.progress_sig.emit(int(float(dn) / int(intel['size']) * 100))
                        pg = str(int(dn / 1000 ** 2)) + ' / ' + str(rounded_size)
                        self.progress.emit(self.states[3] + ' ' + pg)

                if file_hash.hexdigest() == md5:
                    print("verified")
                else:
                    raise Exception("Security error")

            self.progress_sig.emit(0)
            self.progress.emit(self.states[4])
            self.dte = glob_folder
            # Extract encrypted file if password is given or else simply extract
            if not p_skip:
                with py7zr.SevenZipFile(file_out_name, mode='r', password=passwrd) as z:
                    z.extractall(path="./")
            else:
                with py7zr.SevenZipFile(file_out_name, mode='r') as z:
                    z.extractall(path="./")
            self.progress.emit(self.states[5])

            self.progress.emit(self.states[6])

            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def internet_test(self) -> bool:
        """Checks internet connection"""
        network = False

        try:

            socket.create_connection(("1.1.1.1", 53))
            socket.create_connection(("8.8.8.8", 53))
            socket.create_connection(("drive.google.com", 80))
            network = True
        except OSError:
            pass
        return network


glob_folder = ""


class MainWindow(QWidget):
    states = ['Checking connection..', "Starting Download..", "Downloading file ", "Verifying integrity",
              'Extracting files', 'Finalizing', 'Finished']

    def __init__(self):
        global glob_folder
        super(MainWindow, self).__init__()

        self.conn = False
        self.size = 0
        self.offset = 0
        self.obj = Worker()  # no parent needed
        self.thread = QThread()
        available_geometry = self.screen().availableGeometry()
        self.resize(int((available_geometry.width() / 3) - 400),
                    (int(available_geometry.height() / 2 - 600)))
        # self.obj.progress.connect(self)
        self.obj.size.connect(self.setSize)
        self.obj.conn.connect(self.set_connection_status)
        self.obj.error.connect(self.downErr)
        self.obj.progress_sig.connect(self.progupd2)
        self.obj.progress.connect(self.update_progress_bar)
        self.obj.finished.connect(self.thread.quit)
        self.obj.moveToThread(self.thread)
        self.thread.started.connect(self.obj.down)
        self.setStyleSheet("background-color: rgba(20,20,20, 100%); ")
        self.folder = QFileDialog.getExistingDirectory(self, 'Select the folder to extract the file')
        self.setWindowIcon(QIcon(my_path("icon.png")))
        if os.path.isdir(self.folder) and os.access(self.folder, os.W_OK):
            pass
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Operation cancelled")
            msg.setWindowIcon(QIcon(my_path("icon.png")))
            msg.setWindowTitle("Cancelled")
            msg.exec()
            sys.exit(0)

        glob_folder = self.folder
        self.setWindowFlags(Qt.FramelessWindowHint)
        QTimer.singleShot(1000, self.thread.start)
        self.uiSplashDownloader()

    def mousePressEvent(self, event):
        """Handles dragging of borderless window (Set Offset)"""
        if event.button() == Qt.LeftButton:
            self.offset = QPoint(event.position().x(), event.position().y())
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handles dragging of borderless window (Move Window)"""
        if self.offset is not None and event.buttons() == Qt.LeftButton:

            self.move(self.pos() + QPoint(event.scenePosition().x(), event.scenePosition().y()) - self.offset)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handles dragging of borderless window (Release Window)"""
        self.offset = None
        super().mouseReleaseEvent(event)

    def closeEvent(self, event):
        app.quit()

    def update_progress_bar(self, state: str) -> None:
        """Performs operations based on the state of the download progress which is based on the states array"""
        if state == self.states[6]:
            try:
                os.remove(file_out_name)
            except Exception:
                pass
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowIcon(QIcon(my_path("icon.png")))
            # Verify file integrity with md5 checksum if given
            if not md5_skip:
                msg.setText("Successfully downloaded and verified file hash.")
            else:
                msg.setText("Successfully downloaded and extracted the file .")
            msg.setWindowTitle("Done")
            msg.exec()
            sys.exit(0)
        if state == self.states[4]:
            # Set our progress bar to indefinite mode because we cannot yet track extraction progress
            self.pb.setMaximum(0)
            self.pb.setMinimum(0)
            self.pb.setValue(0)
        if state == self.states[5]:

            self.pb.setMinimum(0)
            self.pb.setMaximum(100)
            self.pb.setValue(100)
            time.sleep(0.5)
        self.lb.setText(state)

    def setSize(self, size: str) -> None:
        self.size = size

    def set_connection_status(self, conn: bool) -> None:
        """Closes app if no internet connection"""
        self.conn = conn
        if self.conn == False:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowIcon(QIcon(my_path("icon.png")))
            msg.setText("Error downloading \n No internet connection")
            msg.setWindowTitle("Error")
            msg.exec()
            try:
                os.rmdir("Download")
            except Exception:
                pass
            sys.exit(0)

    def downErr(self, e: str):
        """Handles download error"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowIcon(QIcon(my_path("icon.png")))
        msg.setText("Error downloading " + str(e))
        msg.setWindowTitle("Error")
        msg.exec()
        try:
            os.remove(file_out_name)
        except Exception:
            pass
        sys.exit(0)

    def progupd2(self, percent: int) -> None:
        self.pb.setValue(percent)

    def uiSplashDownloader(self):

        self.l1 = QVBoxLayout()
        self.mainlabel = QLabel("Downloader Z")
        self.ex = QPushButton("Exit")
        self.ex.clicked.connect(self.exr)
        self.lb = QLabel("Loading")
        self.pb = QProgressBar(self)
        self.pb.setRange(0, 100)
        self.mainlabel.setStyleSheet("color : white")

        self.lb.setStyleSheet("color : white ;")

        self.l1.addWidget(self.mainlabel)
        self.l1.addWidget(self.lb)
        self.l1.addWidget(self.pb)
        self.l1.addWidget(self.ex)
        # Load custom font file
        self.mainlabel.setFont(QFont("Baskervville SC", 30))
        self.lb.font().setPointSize(10)
        self.lb.setAlignment(Qt.AlignCenter)
        self.setLayout(self.l1)

    def exr(self) -> None:
        try:
            os.remove(file_out_name)
        except Exception as e:
            print(str(e))
        sys.exit(0)


window = MainWindow()
f = QFontDatabase.addApplicationFont(my_path('BaskervvilleSC-Regular.ttf'))

window.show()

app.setStyle("Fusion")
# Fusion

palette = QPalette()
palette.setColor(QPalette.Window, QColor(53, 53, 53))
palette.setColor(QPalette.WindowText, Qt.white)
palette.setColor(QPalette.Base, QColor(25, 25, 25))
palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
palette.setColor(QPalette.ToolTipBase, Qt.black)
palette.setColor(QPalette.ToolTipText, Qt.white)
palette.setColor(QPalette.Text, Qt.white)
palette.setColor(QPalette.Button, QColor(53, 53, 53))
palette.setColor(QPalette.ButtonText, Qt.white)
palette.setColor(QPalette.BrightText, Qt.red)
palette.setColor(QPalette.Link, QColor(42, 130, 218))
palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
palette.setColor(QPalette.HighlightedText, Qt.white)
app.setPalette(palette)
app.exec()

from PyQt5.QtGui import QImage, QPixmap
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSlot, QTimer, QDate, Qt, QRect
from PyQt5.QtWidgets import QDialog, QMessageBox, QPushButton
from PyQt5 import QtWidgets
from PyQt5.QtCore import QCoreApplication
from tqdm import tqdm
import cv2
import face_recognition
import numpy as np
import datetime
import os
import csv


class Ui_OutputDialog(QDialog):
    def __init__(self):
        super(Ui_OutputDialog, self).__init__()
        loadUi("./outputwindow.ui", self)

        titlelogo = self.findChild(QtWidgets.QLabel, 'picLabel')
        pixmap = QPixmap('mcgs5-splash.png')
        titlelogo.setPixmap(pixmap)
        titlelogo.setScaledContents(True)
        # self.resize(pixmap.width(), pixmap.height())

        # Update time
        now = QDate.currentDate()
        current_date = now.toString('ddd dd MMMM yyyy')
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        self.Date_Label.setText(current_date)
        self.Time_Label.setText(current_time)

        self.image = None

        self.show()

    @pyqtSlot()
    def startVideo(self, camera_name):  # camera source options

        if len(camera_name) == 1:  # this option is for an external usb web cam
            self.capture = cv2.VideoCapture(int(camera_name))
        else:
            self.capture = cv2.VideoCapture(camera_name)
        self.timer = QTimer(self)  # Create Timer
        path = 'ImagesForAccessControl'
        if not os.path.exists(path):
            os.mkdir(path)
        # known face encoding and known face name list
        images = []
        self.people_names = []
        self.encode_list = []
        self.TimeList1 = []
        self.TimeList2 = []
        present_list = os.listdir(path)

        # print(present_list)
        for cl in tqdm(present_list, desc='Split pic extension'):
            cur_img = cv2.imread(f'{path}/{cl}')
            images.append(cur_img)
            self.people_names.append(os.path.splitext(cl)[0])
        for img in tqdm(images, desc='encoding'):
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            boxes = face_recognition.face_locations(img)
            encodes_cur_frame = face_recognition.face_encodings(img, boxes)[0]
            # encode = face_recognition.face_encodings(img)[0]
            self.encode_list.append(encodes_cur_frame)
            # print(encodes_cur_frame)
            # print('Encoding Complete')
        self.timer.timeout.connect(self.update_frame)  # Connect timeout to the output function
        self.timer.start(50)  # emit the timeout() signal at x=40ms
        print('Encoding Complete')

    def face_rec_(self, frame, encode_list_known, class_names):
        # frame: frame from camera
        # encode_list_known: known face encoding
        # class_names: known face names

        # logging to csv
        def log_movement(name):  # name: detected face known or unknown one
            if self.ClockInButton.isChecked():
                self.ClockInButton.setEnabled(False)
                with open('AccessControlLog.csv', 'a') as f:
                    if name != 'unknown':
                        print(name)
                        buttonReply = QMessageBox.question(self, f'Person identified as: {name}',
                                                           f'Are you Clocking {name} In?',
                                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                        if buttonReply == QMessageBox.Yes:

                            date_time_string = datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S")
                            f.writelines(f'\n{name},{date_time_string},Clock In')
                            self.ClockInButton.setChecked(False)

                            self.NameLabel.setText(name)
                            self.StatusLabel.setText('Clocked In')
                            self.HoursLabel.setText('Processing duration')
                            self.MinLabel.setText('')

                            # self.CalculateElapse(name)
                            # print('Yes clicked and detected')
                            self.Time1 = datetime.datetime.now()
                            # print(self.Time1)
                            self.ClockInButton.setEnabled(True)
                        else:
                            print('Not clicked.')
                            self.ClockInButton.setEnabled(True)
                    else:
                        print('Person Unknown')
                        QMessageBox.information(self, "Alert!", "Person not in database")
                        self.ClockInButton.setEnabled(False)
                        # self.ClockOutButton.setEnabled(False)
            elif self.ClockOutButton.isChecked():
                self.ClockOutButton.setEnabled(False)
                with open('AccessControlLog.csv', 'a') as f:
                    if name != 'unknown':
                        buttonReply = QMessageBox.question(self, f'Thank you for coming, {name}.', 'Logging Out?',
                                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                        if buttonReply == QMessageBox.Yes:
                            date_time_string = datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S")
                            f.writelines(f'\n{name},{date_time_string},Clock Out')
                            self.ClockOutButton.setChecked(False)

                            self.NameLabel.setText(name)
                            self.StatusLabel.setText('Clocked Out')
                            self.Time2 = datetime.datetime.now()
                            # print(self.Time2)
                            # calculate time spent
                            self.ElapseList(name)
                            self.TimeList2.append(datetime.datetime.now())
                            CheckInTime = self.TimeList1[-1]
                            CheckOutTime = self.TimeList2[-1]
                            self.ElapseHours = (CheckOutTime - CheckInTime)
                            self.MinLabel.setText(
                                "{:.0f}".format(abs(self.ElapseHours.total_seconds() / 60) % 60) + 'm')
                            self.HoursLabel.setText(
                                "{:.0f}".format(abs(self.ElapseHours.total_seconds() / 60 ** 2)) + 'h')
                            self.ClockOutButton.setEnabled(True)
                        else:
                            print('Not clicked.')
                            self.ClockOutButton.setEnabled(True)
                    else:
                        print('Person Unknown')
                        QMessageBox.information(self, "Alert!", "Person not in database")
                        # self.ClockInButton.setEnabled(False)
                        self.ClockOutButton.setEnabled(False)

        # face recognition
        faces_cur_frame = face_recognition.face_locations(frame)
        encodes_cur_frame = face_recognition.face_encodings(frame, faces_cur_frame)
        # face comparison
        for encodeFace, faceLoc in zip(encodes_cur_frame, faces_cur_frame):
            match = face_recognition.compare_faces(encode_list_known, encodeFace, tolerance=0.50)
            face_dis = face_recognition.face_distance(encode_list_known, encodeFace)
            name = "unknown"
            best_match_index = np.argmin(face_dis)
            # print("s",best_match_index)
            if match[best_match_index]:
                name = class_names[best_match_index].upper()
                y1, x2, y2, x1 = faceLoc
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.rectangle(frame, (x1, y2 - 20), (x2, y2), (255, 0, 0), cv2.FILLED)
                cv2.putText(frame, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
            else:
                # name = class_names[best_match_index].upper()
                y1, x2, y2, x1 = faceLoc
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.rectangle(frame, (x1, y2 - 20), (x2, y2), (255, 0, 0), cv2.FILLED)
                cv2.putText(frame, 'Person Unknown', (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255),
                            1)
            log_movement(name)

        return frame

    # assign time slots to lists(TimeList1 and 2)
    def ElapseList(self, name):
        with open('AccessControlLog.csv', "r") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 2

            Time1 = datetime.datetime.now()
            Time2 = datetime.datetime.now()
            for row in csv_reader:
                for field in row:
                    if field in row:
                        if field == 'Clock In':
                            if row[0] == name:
                                # print(f'\t ROW 0 {row[0]}  ROW 1 {row[1]} ROW2 {row[2]}.')
                                Time1 = (datetime.datetime.strptime(row[1], '%y/%m/%d %H:%M:%S'))
                                self.TimeList1.append(Time1)
                        if field == 'Clock Out':
                            if row[0] == name:
                                # print(f'\t ROW 0 {row[0]}  ROW 1 {row[1]} ROW2 {row[2]}.')
                                Time2 = (datetime.datetime.strptime(row[1], '%y/%m/%d %H:%M:%S'))
                                self.TimeList2.append(Time2)
                                # print(Time2)

    def update_frame(self):
        ret, self.image = self.capture.read()
        self.displayImage(self.image, self.encode_list, self.people_names, 1)

    def displayImage(self, image, encode_list, class_names, window=1):

        # image: frame from camera
        # encode_list: known face encoding list
        # class_names: known face names
        # window: number of window

        image = cv2.resize(image, (640, 480))
        try:
            image = self.face_rec_(image, encode_list, class_names)
        except Exception as e:
            print(e)
        qformat = QImage.Format_Indexed8
        if len(image.shape) == 3:
            if image.shape[2] == 4:
                qformat = QImage.Format_RGBA8888
            else:
                qformat = QImage.Format_RGB888
        outImage = QImage(image, image.shape[1], image.shape[0], image.strides[0], qformat)
        outImage = outImage.rgbSwapped()

        if window == 1:
            self.imgLabel.setPixmap(QPixmap.fromImage(outImage))
            self.imgLabel.setScaledContents(True)

        self.closeButton = self.findChild(QtWidgets.QPushButton, 'clsBtn')
        self.closeButton.clicked.connect(self.close)

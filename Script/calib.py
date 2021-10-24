import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QPixmap, QImage
from mainwindow import *
import picker
import cv2
import numpy as np

# https://qiita.com/kenasman/items/b9ca3beb25ecf87bfb06
# https://qiita.com/montblanc18/items/0188ff680acf028d4b63
# https://takacity.blog.fc2.com/blog-entry-338.html

# create "mainwindow.py" from "mainwindow.ui" using m.bat after editting "mainwindow.ui"

class PickerCalib(QMainWindow):
    global config, config_org

    def __init__(self, parent=None):
        # https://uxmilk.jp/41600
        self.ui = Ui_MainWindow()
        super(PickerCalib, self).__init__(parent)
        self.ui.setupUi(self)
        self.img = []
        self.img_type = 0
        self.image = []
        self.pixmap = []
        self.corner = 0
        self.mouseX = 0
        self.mouseY = 0
        self.fCaptured = False
        self.MouseCursorColor = 0xffffffff
        self.CornerMarkColor = 0xff00ffff
        self.img_size = [0, 0]
        self.window_size = [self.ui.labelView.geometry().width(), self.ui.labelView.geometry().height()]
        self.mag = [1, 1]
#        print(config)
#        print(config_org)
        # initialize tray list
        for tray in config["Tray"]:
            self.ui.comboBoxTrayNumber.addItem(tray)
        self.trayID = self.ui.comboBoxTrayNumber.itemText(0)

        # HSV range
        self.ui.horizontalSliderHU1.setValue(config["HSV_Range"]["Back"]["Upper"]["H"])
        self.ui.horizontalSliderHL1.setValue(config["HSV_Range"]["Back"]["Lower"]["H"])
        self.ui.horizontalSliderHU2.setValue(config["HSV_Range"]["Black"]["Upper"]["H"])
        self.ui.horizontalSliderHL2.setValue(config["HSV_Range"]["Black"]["Lower"]["H"])
        self.ui.horizontalSliderSU1.setValue(config["HSV_Range"]["Back"]["Upper"]["S"])
        self.ui.horizontalSliderSL1.setValue(config["HSV_Range"]["Back"]["Lower"]["S"])
        self.ui.horizontalSliderSU2.setValue(config["HSV_Range"]["Black"]["Upper"]["S"])
        self.ui.horizontalSliderSL2.setValue(config["HSV_Range"]["Black"]["Lower"]["S"])
        self.ui.horizontalSliderVU1.setValue(config["HSV_Range"]["Back"]["Upper"]["V"])
        self.ui.horizontalSliderVL1.setValue(config["HSV_Range"]["Back"]["Lower"]["V"])
        self.ui.horizontalSliderVU2.setValue(config["HSV_Range"]["Black"]["Upper"]["V"])
        self.ui.horizontalSliderVL2.setValue(config["HSV_Range"]["Black"]["Lower"]["V"])

        self.update_tray_info(self.trayID)

        self.ui.pushButtonMoveX.clicked.connect(self.onMoveX)
        self.ui.pushButtonMoveY.clicked.connect(self.onMoveY)
        self.ui.pushButtonMoveZ.clicked.connect(self.onMoveZ)
        self.ui.comboBoxTrayNumber.currentIndexChanged.connect(self.onTrayNumberChanged)
        self.ui.pushButtonAddTray.clicked.connect(self.onAddTray)
        self.ui.pushButtonDeleteTray.clicked.connect(self.onDeleteTray)

        self.ui.pushButtonGetTrayCamera1.clicked.connect(self.onGetTrayCamera1)
        self.ui.pushButtonGetTrayCamera2.clicked.connect(self.onGetTrayCamera2)
        self.ui.pushButtonGetTrayCamera3.clicked.connect(self.onGetTrayCamera3)
        self.ui.pushButtonGetTrayCamera4.clicked.connect(self.onGetTrayCamera4)

        self.ui.pushButtonCapture.clicked.connect(self.onCapture)
        self.ui.pushButtonSave.clicked.connect(self.onSave)
        self.ui.pushButtonQuit.clicked.connect(self.onQuit)
        self.ui.pushButtonMoveNextBaseCorner.clicked.connect(self.onMoveNextBaseCorner)
        self.ui.pushButtonMoveUp.clicked.connect(self.onMoveUp)
        self.ui.pushButtonMoveTrayCamera.clicked.connect(self.onMoveTrayCamera)
        self.ui.radioButtonRaw.clicked.connect(self.onSelectRaw)
        self.ui.radioButtonBack.clicked.connect(self.onSelectBack)
        self.ui.radioButtonBlack.clicked.connect(self.onSelectBlack)
        self.ui.radioButtonComponent.clicked.connect(self.onSelectComponent)
        self.ui.pushButtonCheckCmp.clicked.connect(self.onSelectComponentChk)
        self.ui.pushButtonMoveTrayCorner1.clicked.connect(self.onMoveTrayCorner1)
        self.ui.pushButtonMoveTrayCorner2.clicked.connect(self.onMoveTrayCorner2)
        self.ui.pushButtonMoveTrayCorner3.clicked.connect(self.onMoveTrayCorner3)
        self.ui.pushButtonMoveTrayCorner4.clicked.connect(self.onMoveTrayCorner4)
        self.ui.horizontalSliderHU1.valueChanged.connect(self.onHU1_Changed)
        self.ui.horizontalSliderHL1.valueChanged.connect(self.onHL1_Changed)
        self.ui.horizontalSliderHU2.valueChanged.connect(self.onHU2_Changed)
        self.ui.horizontalSliderHL2.valueChanged.connect(self.onHL2_Changed)
        self.ui.horizontalSliderSU1.valueChanged.connect(self.onSU1_Changed)
        self.ui.horizontalSliderSL1.valueChanged.connect(self.onSL1_Changed)
        self.ui.horizontalSliderSU2.valueChanged.connect(self.onSU2_Changed)
        self.ui.horizontalSliderSL2.valueChanged.connect(self.onSL2_Changed)
        self.ui.horizontalSliderVU1.valueChanged.connect(self.onVU1_Changed)
        self.ui.horizontalSliderVL1.valueChanged.connect(self.onVL1_Changed)
        self.ui.horizontalSliderVU2.valueChanged.connect(self.onVU2_Changed)
        self.ui.horizontalSliderVL2.valueChanged.connect(self.onVL2_Changed)
        self.ui.pushButtonMoveDispenerHeadX.clicked.connect(self.onMoveSetDispenserHeadOffsetX)
        self.ui.pushButtonMoveDispenerHeadY.clicked.connect(self.onMoveSetDispenserHeadOffsetY)
        self.ui.pushButtonMoveDispenerHeadZ.clicked.connect(self.onMoveSetDispenserHeadOffsetZ)

        self.ui.pushButtonTrayAutoCalcFrom1.clicked.connect(self.onTrayAutoCalcFrom1)
        self.ui.plainTextEditDispenserOffsetX.setPlainText(str(config["Physical"]["DispenserHeadOffset"][0]))
        self.ui.plainTextEditDispenserOffsetY.setPlainText(str(config["Physical"]["DispenserHeadOffset"][1]))
        self.ui.plainTextEditDispenserOffsetZ.setPlainText(str(config["Physical"]["DispenserHeadOffset"][2]))
        self.show()

    def update_tray_info(self, trayID):
        # Compnoent Area
        self.ui.plainTextEditAreaCompL.setPlainText(str(config["Tray"][trayID]["Area"]["Component"]["Lower"]))
        self.ui.plainTextEditAreaCompU.setPlainText(str(config["Tray"][trayID]["Area"]["Component"]["Upper"]))
        self.ui.plainTextEditAreaBlackL.setPlainText(str(config["Tray"][trayID]["Area"]["Black"]["Lower"]))
        self.ui.plainTextEditAreaBlackU.setPlainText(str(config["Tray"][trayID]["Area"]["Black"]["Upper"]))
        # Corner Camera
        self.ui.plainTextEditPosCamera1X.setPlainText(str(config["Tray"][trayID]["Corner"]["Camera"]["UpperLeft"][0]))
        self.ui.plainTextEditPosCamera1Y.setPlainText(str(config["Tray"][trayID]["Corner"]["Camera"]["UpperLeft"][1]))
        self.ui.plainTextEditPosCamera2X.setPlainText(str(config["Tray"][trayID]["Corner"]["Camera"]["UpperRight"][0]))
        self.ui.plainTextEditPosCamera2Y.setPlainText(str(config["Tray"][trayID]["Corner"]["Camera"]["UpperRight"][1]))
        self.ui.plainTextEditPosCamera3X.setPlainText(str(config["Tray"][trayID]["Corner"]["Camera"]["LowerRight"][0]))
        self.ui.plainTextEditPosCamera3Y.setPlainText(str(config["Tray"][trayID]["Corner"]["Camera"]["LowerRight"][1]))
        self.ui.plainTextEditPosCamera4X.setPlainText(str(config["Tray"][trayID]["Corner"]["Camera"]["LowerLeft"][0]))
        self.ui.plainTextEditPosCamera4Y.setPlainText(str(config["Tray"][trayID]["Corner"]["Camera"]["LowerLeft"][1]))
        # Corner Real
        self.ui.plainTextEditPosReal1X.setPlainText(str(config["Tray"][trayID]["Corner"]["Real"]["UpperLeft"][0]))
        self.ui.plainTextEditPosReal1Y.setPlainText(str(config["Tray"][trayID]["Corner"]["Real"]["UpperLeft"][1]))
        self.ui.plainTextEditPosReal2X.setPlainText(str(config["Tray"][trayID]["Corner"]["Real"]["UpperRight"][0]))
        self.ui.plainTextEditPosReal2Y.setPlainText(str(config["Tray"][trayID]["Corner"]["Real"]["UpperRight"][1]))
        self.ui.plainTextEditPosReal3X.setPlainText(str(config["Tray"][trayID]["Corner"]["Real"]["LowerRight"][0]))
        self.ui.plainTextEditPosReal3Y.setPlainText(str(config["Tray"][trayID]["Corner"]["Real"]["LowerRight"][1]))
        self.ui.plainTextEditPosReal4X.setPlainText(str(config["Tray"][trayID]["Corner"]["Real"]["LowerLeft"][0]))
        self.ui.plainTextEditPosReal4Y.setPlainText(str(config["Tray"][trayID]["Corner"]["Real"]["LowerLeft"][1]))
        # Camera
        self.ui.plainTextEditPosCameraX.setPlainText(str(config["Tray"][trayID]["Camera"][0]))
        self.ui.plainTextEditPosCameraY.setPlainText(str(config["Tray"][trayID]["Camera"][1]))
        self.ui.plainTextEditPosCameraZ.setPlainText(str(config["Camera"]["Height"]))

    # HUV sliders
    def onHU1_Changed(self, value):
        config["HSV_Range"]["Back"]["Upper"]["H"] = value
        self.ShowImage()
    def onHL1_Changed(self, value):
        config["HSV_Range"]["Back"]["Lower"]["H"] = value
        self.ShowImage()
    def onHU2_Changed(self, value):
        config["HSV_Range"]["Black"]["Upper"]["H"] = value
        self.ShowImage()
    def onHL2_Changed(self, value):
        config["HSV_Range"]["Black"]["Upper"]["H"] = value
        self.ShowImage()
    def onSU1_Changed(self, value):
        config["HSV_Range"]["Back"]["Upper"]["S"] = value
        self.ShowImage()
    def onSL1_Changed(self, value):
        config["HSV_Range"]["Back"]["Lower"]["S"] = value
        self.ShowImage()
    def onSU2_Changed(self, value):
        config["HSV_Range"]["Black"]["Upper"]["S"] = value
        self.ShowImage()
    def onSL2_Changed(self, value):
        config["HSV_Range"]["Black"]["Lower"]["S"] = value
        self.ShowImage()
    def onVU1_Changed(self, value):
        config["HSV_Range"]["Back"]["Upper"]["V"] = value
        self.ShowImage()
    def onVL1_Changed(self, value):
        config["HSV_Range"]["Back"]["Lower"]["V"] = value
        self.ShowImage()
    def onVU2_Changed(self, value):
        config["HSV_Range"]["Black"]["Upper"]["V"] = value
        self.ShowImage()
    def onVL2_Changed(self, value):
        config["HSV_Range"]["Black"]["Lower"]["V"] = value
        self.ShowImage()

    def onTrayNumberChanged(self):
        self.trayID = self.ui.comboBoxTrayNumber.currentText()
        self.update_tray_info(self.trayID)

    def onAddTray(self):
        trayID = self.ui.plainTextEditTrayNumber.toPlainText()
        self.ui.comboBoxTrayNumber.addItem(trayID)
        config["Tray"][trayID] = config["Tray"]["1"]
    def onDeleteTray(self):
        trayID = self.ui.comboBoxTrayNumber.currentText()
        print("deleting "+trayID)
        del config["Tray"][trayID]
        self.ui.comboBoxTrayNumber.removeItem(self.ui.comboBoxTrayNumber.currentIndex())
            
    # image type selection
    def onSelectRaw(self):
        self.img_type = 0
        self.ShowImage()
        
    def onSelectBack(self):
        self.img_type = 1
        self.ShowImage()
        
    def onSelectBlack(self):
        self.img_type = 2
        self.ShowImage()
        
    def onSelectComponent(self):
        self.img_type = 3
        self.ShowImage()

    def onSelectComponentChk(self):
        self.img_type = 4
        self.ShowImage()

    
    # draw cross
    def DrawCrossOnBase(self, x, y):
        '''
        Zpos_draw = 45
        Zpos_move = 80
        L_cross = 5
        picker.move_Z(Zpos_move)
        picker.move_XY(x, y)
        picker.move_Z(Zpos_draw)
        picker.move_XY(x - L_cross, y)
        picker.move_Z(Zpos_move)
        picker.move_XY(x, y)
        picker.move_Z(Zpos_draw)
        picker.move_XY(x + L_cross, y)
        picker.move_Z(Zpos_move)
        picker.move_XY(x, y)
        picker.move_Z(Zpos_draw)
        picker.move_XY(x, y - L_cross)
        picker.move_Z(Zpos_move)
        picker.move_XY(x, y)
        picker.move_Z(Zpos_draw)
        picker.move_XY(x, y + L_cross)
        picker.move_Z(Zpos_move)
        '''
        picker.move_Z(50)
        picker.move_XY(x, y)
        picker.move_Z(0)
        #picker.move_Z(10)
        #picker.move_Z(15) # 3mm for position calibaration with base board

    def onMoveUp(self):
        picker.move_Z(50)
        if (self.corner == 0):
            picker.move_Y(30)
        elif self.corner == 1:
            picker.move_Y(30)
        elif self.corner == 2:
            picker.move_Y(225)
        else:
            picker.move_Y(225)

        
    # move to base corner
    def onMoveNextBaseCorner(self):
        self.corner = (self.corner + 1) % 4
        print("move to base corner"+str(self.corner))
        if (self.corner == 0):
            self.DrawCrossOnBase(0, 0)
        elif self.corner == 1:
            self.DrawCrossOnBase(200, 0) # for position calibration with base board
#            self.DrawCrossOnBase(230, 0) # for height calibration without base board
        elif self.corner == 2:
            self.DrawCrossOnBase(200, 195) # for position calibration with base board
#            self.DrawCrossOnBase(230, 195) # for height calibration without base board
        else:
            self.DrawCrossOnBase(5, 195)

    # move to tray
    def onMoveTrayCamera(self):
        picker.light_control(True)
        print("move to tray camera " + self.trayID)
        config["Tray"][self.trayID]["Camera"][0] = float(self.ui.plainTextEditPosCameraX.toPlainText())
        config["Tray"][self.trayID]["Camera"][1] = float(self.ui.plainTextEditPosCameraY.toPlainText())
        config["Camera"]["Height"] = float(self.ui.plainTextEditPosCameraZ.toPlainText())
        picker.move_camera(self.trayID)

    def onMoveTrayCorner1(self):
        config["Tray"][self.trayID]["Corner"]["Real"]["UpperLeft"][0] = float(self.ui.plainTextEditPosReal1X.toPlainText())
        config["Tray"][self.trayID]["Corner"]["Real"]["UpperLeft"][1] = float(self.ui.plainTextEditPosReal1Y.toPlainText())
        picker.move_Z(config["Physical"]["Height"]["Motion"])
        picker.move_XY(config["Tray"][self.trayID]["Corner"]["Real"]["UpperLeft"][0], config["Tray"][self.trayID]["Corner"]["Real"]["UpperLeft"][1])
    def onMoveTrayCorner2(self):
        config["Tray"][self.trayID]["Corner"]["Real"]["UpperRight"][0] = float(self.ui.plainTextEditPosReal2X.toPlainText())
        config["Tray"][self.trayID]["Corner"]["Real"]["UpperRight"][1] = float(self.ui.plainTextEditPosReal2Y.toPlainText())
        picker.move_Z(config["Physical"]["Height"]["Motion"])
        picker.move_XY(config["Tray"][self.trayID]["Corner"]["Real"]["UpperRight"][0], config["Tray"][self.trayID]["Corner"]["Real"]["UpperRight"][1])
    def onMoveTrayCorner3(self):
        config["Tray"][self.trayID]["Corner"]["Real"]["LowerRight"][0] = float(self.ui.plainTextEditPosReal3X.toPlainText())
        config["Tray"][self.trayID]["Corner"]["Real"]["LowerRight"][1] = float(self.ui.plainTextEditPosReal3Y.toPlainText())
        picker.move_Z(config["Physical"]["Height"]["Motion"])
        picker.move_XY(config["Tray"][self.trayID]["Corner"]["Real"]["LowerRight"][0], config["Tray"][self.trayID]["Corner"]["Real"]["LowerRight"][1])
    def onMoveTrayCorner4(self):
        config["Tray"][self.trayID]["Corner"]["Real"]["LowerLeft"][0] = float(self.ui.plainTextEditPosReal4X.toPlainText())
        config["Tray"][self.trayID]["Corner"]["Real"]["LowerLeft"][1] = float(self.ui.plainTextEditPosReal4Y.toPlainText())
        picker.move_Z(config["Physical"]["Height"]["Motion"])
        picker.move_XY(config["Tray"][self.trayID]["Corner"]["Real"]["LowerLeft"][0], config["Tray"][self.trayID]["Corner"]["Real"]["LowerLeft"][1])

    # manual move
    def onMoveX(self):
        v = float(self.ui.plainTextEditManualMove.toPlainText())
        picker.move_X(v)
    def onMoveY(self):
        v = float(self.ui.plainTextEditManualMove.toPlainText())
        picker.move_Y(v)
    def onMoveZ(self):
        v = float(self.ui.plainTextEditManualMove.toPlainText())
        picker.move_Z(v)
        
    # system
    def onQuit(self):
        #picker.light_control(False)
        sys.exit()

    def onSave(self):
        '''
        for trayID in config["Tray"]:
            config["Tray"][trayID]["Area"]["Component"]["Lower"] = int(self.ui.plainTextEditAreaCompL.toPlainText())
            config["Tray"][trayID]["Area"]["Component"]["Upper"] = int(self.ui.plainTextEditAreaCompU.toPlainText())
            config["Tray"][trayID]["Area"]["Black"]["Lower"] = int(self.ui.plainTextEditAreaBlackL.toPlainText())
            config["Tray"][trayID]["Area"]["Black"]["Upper"] = int(self.ui.plainTextEditAreaBlackU.toPlainText())
            config["Tray"][trayID]["Corner"]["Camera"]["UpperLeft"][0] = float(self.ui.plainTextEditPosCamera1X.toPlainText())
            config["Tray"][trayID]["Corner"]["Camera"]["UpperLeft"][1] = float(self.ui.plainTextEditPosCamera1Y.toPlainText())
            config["Tray"][trayID]["Corner"]["Camera"]["UpperRight"][0] = float(self.ui.plainTextEditPosCamera2X.toPlainText())
            config["Tray"][trayID]["Corner"]["Camera"]["UpperRight"][1] = float(self.ui.plainTextEditPosCamera2Y.toPlainText())
            config["Tray"][trayID]["Corner"]["Camera"]["LowerRight"][0] = float(self.ui.plainTextEditPosCamera3X.toPlainText())
            config["Tray"][trayID]["Corner"]["Camera"]["LowerRight"][1] = float(self.ui.plainTextEditPosCamera3Y.toPlainText())
            config["Tray"][trayID]["Corner"]["Camera"]["LowerLeft"][0] = float(self.ui.plainTextEditPosCamera4X.toPlainText())
            config["Tray"][trayID]["Corner"]["Camera"]["LowerLeft"][1] = float(self.ui.plainTextEditPosCamera4Y.toPlainText())
            config["Tray"][trayID]["Corner"]["Real"]["UpperLeft"][0] = float(self.ui.plainTextEditPosReal1X.toPlainText())
            config["Tray"][trayID]["Corner"]["Real"]["UpperLeft"][1] = float(self.ui.plainTextEditPosReal1Y.toPlainText())
            config["Tray"][trayID]["Corner"]["Real"]["UpperRight"][0] = float(self.ui.plainTextEditPosReal2X.toPlainText())
            config["Tray"][trayID]["Corner"]["Real"]["UpperRight"][1] = float(self.ui.plainTextEditPosReal2Y.toPlainText())
            config["Tray"][trayID]["Corner"]["Real"]["LowerRight"][0] = float(self.ui.plainTextEditPosReal3X.toPlainText())
            config["Tray"][trayID]["Corner"]["Real"]["LowerRight"][1] = float(self.ui.plainTextEditPosReal3Y.toPlainText())
            config["Tray"][trayID]["Corner"]["Real"]["LowerLeft"][0] = float(self.ui.plainTextEditPosReal4X.toPlainText())
            config["Tray"][trayID]["Corner"]["Real"]["LowerLeft"][1] = float(self.ui.plainTextEditPosReal4Y.toPlainText())
            config["Tray"][trayID]["Camera"][0] = float(self.ui.plainTextEditPosCameraX.toPlainText())
            config["Tray"][trayID]["Camera"][1] = float(self.ui.plainTextEditPosCameraY.toPlainText())
        '''
        config["HSV_Range"]["Back"]["Upper"]["H"] = self.ui.horizontalSliderHU1.value()
        config["HSV_Range"]["Back"]["Lower"]["H"] = self.ui.horizontalSliderHL1.value()
        config["HSV_Range"]["Back"]["Upper"]["S"] = self.ui.horizontalSliderSU1.value()
        config["HSV_Range"]["Back"]["Lower"]["S"] = self.ui.horizontalSliderSL1.value()
        config["HSV_Range"]["Back"]["Upper"]["V"] = self.ui.horizontalSliderVU1.value()
        config["HSV_Range"]["Back"]["Lower"]["V"] = self.ui.horizontalSliderVL1.value()
        config["HSV_Range"]["Black"]["Upper"]["H"] = self.ui.horizontalSliderHU2.value()
        config["HSV_Range"]["Black"]["Lower"]["H"] = self.ui.horizontalSliderHL2.value()
        config["HSV_Range"]["Black"]["Upper"]["S"] = self.ui.horizontalSliderSU2.value()
        config["HSV_Range"]["Black"]["Lower"]["S"] = self.ui.horizontalSliderSL2.value()
        config["HSV_Range"]["Black"]["Upper"]["V"] = self.ui.horizontalSliderVU2.value()
        config["HSV_Range"]["Black"]["Lower"]["V"] = self.ui.horizontalSliderVL2.value()
        config["Camera"]["Height"] = float(self.ui.plainTextEditPosCameraZ.toPlainText())
        # picker.save_config(config_org, "config.bak")
        picker.save_config(config)

    def onCapture(self):
        self.fCaptured = True
        #self.img = picker.capture(False, 0, 0) # load raw.png instead of camera
        self.img = picker.capture(True, 0) # camera capture
        self.img_size = [self.img.shape[1], self.img.shape[0]]
        self.mag = [self.img_size[0] / self.window_size[0], self.img_size[1] / self.window_size[1]]
        self.ShowImage()

    def draw_cross(self, x, y, color):
        for d in range(5):
            self.image.setPixel(int(x)+d, int(y), color)
            self.image.setPixel(int(x)-d, int(y), color)
            self.image.setPixel(int(x), int(y)-d, color)
            self.image.setPixel(int(x), int(y)+d, color)
   
    def ShowImage(self):
        if self.fCaptured == True:
            if self.img_type == 0:
                # raw
                self.image = QImage(self.img.data, self.img.shape[1], self.img.shape[0], QImage.Format_BGR888)
                self.draw_cross(float(self.ui.plainTextEditPosCamera1X.toPlainText()), float(self.ui.plainTextEditPosCamera1Y.toPlainText()), self.CornerMarkColor)
                self.draw_cross(float(self.ui.plainTextEditPosCamera2X.toPlainText()), float(self.ui.plainTextEditPosCamera2Y.toPlainText()), self.CornerMarkColor)
                self.draw_cross(float(self.ui.plainTextEditPosCamera3X.toPlainText()), float(self.ui.plainTextEditPosCamera3Y.toPlainText()), self.CornerMarkColor)
                self.draw_cross(float(self.ui.plainTextEditPosCamera4X.toPlainText()), float(self.ui.plainTextEditPosCamera4Y.toPlainText()), self.CornerMarkColor)
                self.DrawPixmap()
                #config["Tray"][self.trayID]["MatrixToImage"] = picker.calc_transform_to_image(self.trayID).tolist()
                #config["Tray"][self.trayID]["MatrixToReal"] = picker.calc_transform_to_real(self.trayID).tolist()
            
            elif self.img_type == 1:
                # back digitized
                self.image = QImage(picker.digitize(self.img, config["HSV_Range"]["Back"]).data, self.img.shape[1], self.img.shape[0], QImage.Format_Grayscale8)
            elif self.img_type == 2:
                # black digitized
                self.image = QImage(picker.digitize(self.img, config["HSV_Range"]["Black"]).data, self.img.shape[1], self.img.shape[0], QImage.Format_Grayscale8)
            elif self.img_type == 3 or self.img_type == 4:
                cmp, img_cmp = picker.create_component_list(self.img, self.trayID, 2) # tray_margin=2mm
                self.image = QImage(img_cmp, img_cmp.shape[1], img_cmp.shape[0], QImage.Format_BGR888)
                print("Componet List:")
                for c in cmp:
                    print(" ({0:.2f}, {1:.2f}), ang={2:.2f} / front={3:})".format(c[0],c[1], c[2], c[3]))
                    if self.img_type == 4:
                        picker.move_XY(c[0], c[1])
                        if c[3] == True:
                            picker.move_Z(35) # front-sided component
                        else:
                            picker.move_Z(50) # back-sided component
                        picker.move_Z(80)
            self.DrawPixmap()

    def DrawPixmap(self):
        self.pixmap = QPixmap.fromImage(self.image)

        # https://yamamon1010.hatenablog.jp/entry/qlabel_resize_image
        self.pixmap = self.pixmap.scaled(640, 480, Qt.KeepAspectRatio, Qt.FastTransformation)
        self.ui.labelView.setPixmap(self.pixmap)
        pass

    def mousePressEvent(self, event):
        if (self.fCaptured == True):
            x = int((event.x() - self.ui.labelView.geometry().topLeft().x()) * self.mag[0])
            y = int((event.y() - self.ui.labelView.geometry().topLeft().y()) * self.mag[1])
            cursor_size = 5
            if cursor_size < x < self.img_size[0] - cursor_size and cursor_size < y < self.img_size[1]:
                self.ui.labelMousePos.setText("({0:d}, {1:d})".format(x, y))
                self.mouseX = x
                self.mouseY = y
                self.draw_cross(x, y, self.MouseCursorColor)
                self.DrawPixmap()

    def onGetTrayCamera1(self):
        self.ui.plainTextEditPosCamera1X.setPlainText(str(self.mouseX))
        self.ui.plainTextEditPosCamera1Y.setPlainText(str(self.mouseY))
        config["Tray"][self.trayID]["Corner"]["Camera"]["UpperLeft"][0] = float(self.ui.plainTextEditPosCamera1X.toPlainText())
        config["Tray"][self.trayID]["Corner"]["Camera"]["UpperLeft"][1] = float(self.ui.plainTextEditPosCamera1Y.toPlainText())
    def onGetTrayCamera2(self):
        self.ui.plainTextEditPosCamera2X.setPlainText(str(self.mouseX))
        self.ui.plainTextEditPosCamera2Y.setPlainText(str(self.mouseY))
        config["Tray"][self.trayID]["Corner"]["Camera"]["UpperRight"][0] = float(self.ui.plainTextEditPosCamera2X.toPlainText())
        config["Tray"][self.trayID]["Corner"]["Camera"]["UpperRight"][1] = float(self.ui.plainTextEditPosCamera2Y.toPlainText())
    def onGetTrayCamera3(self):
        self.ui.plainTextEditPosCamera3X.setPlainText(str(self.mouseX))
        self.ui.plainTextEditPosCamera3Y.setPlainText(str(self.mouseY))
        config["Tray"][self.trayID]["Corner"]["Camera"]["LowerRight"][0] = float(self.ui.plainTextEditPosCamera3X.toPlainText())
        config["Tray"][self.trayID]["Corner"]["Camera"]["LowerRight"][1] = float(self.ui.plainTextEditPosCamera3Y.toPlainText())
    def onGetTrayCamera4(self):
        self.ui.plainTextEditPosCamera4X.setPlainText(str(self.mouseX))
        self.ui.plainTextEditPosCamera4Y.setPlainText(str(self.mouseY))
        config["Tray"][self.trayID]["Corner"]["Camera"]["LowerLeft"][0] = float(self.ui.plainTextEditPosCamera4X.toPlainText())
        config["Tray"][self.trayID]["Corner"]["Camera"]["LowerLeft"][1] = float(self.ui.plainTextEditPosCamera4Y.toPlainText())
        
    def onMoveSetDispenserHeadOffsetX(self):
        # X-offset = X at touching upper-left corner of board
        off = float(self.ui.plainTextEditDispenserOffsetX.toPlainText())
        picker.move_X(off)
        config["Physical"]["DispenserHeadOffset"][0] = off

    def onMoveSetDispenserHeadOffsetY(self):
        # Y-offset = Y at touching upper-left corner of board
        off = float(self.ui.plainTextEditDispenserOffsetY.toPlainText())
        picker.move_Y(200 + off)
        config["Physical"]["DispenserHeadOffset"][1] = off
    def onMoveSetDispenserHeadOffsetZ(self):
        # Z-offset = Z at touching surface of base
        off = float(self.ui.plainTextEditDispenserOffsetZ.toPlainText())
        picker.move_Z(off)
        config["Physical"]["DispenserHeadOffset"][2] = off

    def onTrayAutoCalcFrom1(self):
        for tr in range(2, 13):
            trs = str(tr)
            tray_pitch = (36, 29)
            config["Tray"][trs]["Corner"]["Camera"] = config["Tray"]["1"]["Corner"]["Camera"]
            x = (tr - 1) % 6
            y = int((tr - 1) / 6)
            config["Tray"][trs]["Corner"]["Real"]["UpperLeft"][0] = config["Tray"]["1"]["Corner"]["Real"]["UpperLeft"][0] + tray_pitch[0] * x
            config["Tray"][trs]["Corner"]["Real"]["UpperRight"][0] = config["Tray"]["1"]["Corner"]["Real"]["UpperRight"][0] + tray_pitch[0] * x
            config["Tray"][trs]["Corner"]["Real"]["LowerRight"][0] = config["Tray"]["1"]["Corner"]["Real"]["LowerRight"][0] + tray_pitch[0] * x
            config["Tray"][trs]["Corner"]["Real"]["LowerLeft"][0] = config["Tray"]["1"]["Corner"]["Real"]["LowerLeft"][0] + tray_pitch[0] * x
            config["Tray"][trs]["Corner"]["Real"]["UpperLeft"][1] = config["Tray"]["1"]["Corner"]["Real"]["UpperLeft"][1] + tray_pitch[1] * y
            config["Tray"][trs]["Corner"]["Real"]["UpperRight"][1] = config["Tray"]["1"]["Corner"]["Real"]["UpperRight"][1] + tray_pitch[1] * y
            config["Tray"][trs]["Corner"]["Real"]["LowerRight"][1] = config["Tray"]["1"]["Corner"]["Real"]["LowerRight"][1] + tray_pitch[1] * y
            config["Tray"][trs]["Corner"]["Real"]["LowerLeft"][1] = config["Tray"]["1"]["Corner"]["Real"]["LowerLeft"][1] + tray_pitch[1] * y
            
if __name__=="__main__":
    config = picker.load_config()
    #config_org = config.copy()
    app = QApplication(sys.argv)
    w = PickerCalib()
    w.show()
    sys.exit(app.exec_())

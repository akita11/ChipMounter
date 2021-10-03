#import cv2
import math
import numpy as np
import time
#import json
import csv
import sys
import picker
import operator

config = picker.load_config()

args = sys.argv
if len(args) > 1:
    filename = args[1]
else:
    filename = 'pos.csv'

# upper-left corenr of PCB
x0, y0 = (0.0, 0.0)

# PCB size
sx, sy = (99.06, 88.9)

# PCB left-side corner on Base
bx0, by0 = (0, 200)

# read top side of PCB (set False for bottom side)
top_side = True
#top_side = False

r = csv.reader(open(filename))
n = 0

header = next(r)

# https://www.sejuku.net/blog/23710
# https://teratail.com/questions/217581
# https://www.sejuku.net/blog/23710

# tray pitch = (x, y)=(34mm, 0mm)

# x, y, ang, side, tray, frontside
rows = [[float(row[3]), float(row[4]), float(row[5]), row[6], row[7], row[8]] for row in r]

row_sorted = sorted(rows, key=operator.itemgetter(0)) # sort by 1st (x)

picker.light_control(True)
picker.pump_control(True)

def ask_component_check(trayID):
    picker.pump_control(False)
    picker.move_Z(200)
    input("check component tray {0:s}, and try next to Enter".format(trayID))
    picker.move_camera(trayID)
    picker.pump_control(True)

for row in row_sorted:
    #ref = row[0]
    #val = row[1]
    tx = float(row[0]) - x0 + bx0
    ty = float(row[1]) - y0 + by0
    tang = float(row[2])
    side = row[3]
    if side == 'bottom':
        tx = sx - tx
        tang = -tang
    tray = int(row[4])
    frontside = int(row[5])
    if (top_side == True and side == 'top') or (top_side == False and side == 'bottom'):
        if tray > 0:
            trayID = str(tray)
            #print("moving")
            picker.move_camera(trayID)
            #input("Press Enter when camera ready")
            #print("done")
            #print("finding components")
            tray_margin = 1.0 # [mm]
            fPlaced = False
            while fPlaced == False:
                cmp = picker.find_component(trayID, tray_margin)
                if len(cmp) == 0:
                    print("no componet in tray {0:s}".format(trayID))
                    ask_component_check(trayID)
                else:
                    while fPlaced == False:
                        print("{0:d} componets in tray {1:s}".format(len(cmp), trayID))
                        for cmpt in cmp:
                            if fPlaced == False:
                                if frontside == 0 or (frontside == 1 and cmpt[3] == True):
                                    print("tray{0:d} / ({1:.2f} {2:.2f} / {3:.2f}) -> ({4:.2f}, {5:.2f}) / {6:.1f}".format(tray, cmpt[0], cmpt[1], cmpt[2], tx, ty, tang))
                                    picker.pick(cmpt[0], cmpt[1], cmpt[2])
                                    picker.place(tx, ty, tang)
                                    fPlaced = True
                        if fPlaced == False:
                            # found components, but no available components
                            print("no available componet in tray {0:s}".format(trayID))
                            ask_component_check(trayID)
                            cmp = picker.find_component(trayID, tray_margin)
                        
picker.move_Z(200)
picker.move_XY(0, 220)
picker.pump_control(False)
picker.light_control(False)

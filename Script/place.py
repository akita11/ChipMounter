# ToDo: keyboard calibration?

import math
import numpy as np
import time
import csv
import sys
import picker
import operator
from pynput import keyboard

# read top side of PCB (set False for bottom side)
#top_side = True
top_side = False

# specify target area on PCB (-1 if no specify)
xmin = 0
xmax = 18
ymin = -22
ymax = 0

# place test only
fPlaceTest = 1

#----------------------------
offset = [0, 0, 0]

args = sys.argv
if len(args) > 2:
    pos_filename = args[1]
    board_filename = args[2]
else:
    pos_filename = 'pos.csv'
    board_filename = 'board.txt'

print("* Pos file:", pos_filename)
print("* Board file:", board_filename)

config = picker.load_config()
board = picker.load_board_config(board_filename)

x0, y0 = board["Origin"] # upper-left corenr of PCB in CAD
sx, sy = board["Size"] # PCB size
board_thickness = board["Thickness"]

# Machine Parameters
bx0, by0 = (0, 200) # PCB left-side corner on Base

r = csv.reader(open(pos_filename))
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
if fPlaceTest != 1:
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
    tx0 = float(row[0])
    ty0 = float(row[1])
    tang = float(row[2])
    side = row[3]
    if side == 'bottom':
        tx0 = sx - tx0
        tang = -tang
    tray = int(row[4])
    frontside = int(row[5]) # 0=both side, 1=top only, 2=in tape
    if ((xmin != 0 and tx0 >= xmin) or (xmin == 0)) and ((xmax != 0 and tx0 <= xmax) or (xmax == 0)) and ((ymin != 0 and ty0 >= ymin) or (ymin == 0)) and ((ymax != 0 and ty0 <= ymax) or (ymax == 0)) and tray > 0:
        tx = tx0 - x0 + bx0
        ty = ty0 - y0 + by0
        if (top_side == True and side == 'top') or (top_side == False and side == 'bottom'):
            trayID = str(tray)
            if fPlaceTest == 1:
                picker.place(tx, ty, tang, board_thickness)
                #print(tx0, ty0, side,tray)
            else:
                if frontside == 2:
                    # no camera, component is assumed to be placed at center of the tray
                    px = (config["Tray"][trayID]["Corner"]["Real"]["UpperLeft"][0] + config["Tray"][trayID]["Corner"]["Real"]["UpperRight"][0] + config["Tray"][trayID]["Corner"]["Real"]["LowerRight"][0] + config["Tray"][trayID]["Corner"]["Real"]["LowerLeft"][0]) / 4
                    py = (config["Tray"][trayID]["Corner"]["Real"]["UpperLeft"][1] + config["Tray"][trayID]["Corner"]["Real"]["UpperRight"][1] + config["Tray"][trayID]["Corner"]["Real"]["LowerRight"][1] + config["Tray"][trayID]["Corner"]["Real"]["LowerLeft"][1]) / 4
                    px = px - 1 # component center is 1mm left from tray center
                    pa = 0 # angle is assumed to be 0
                    picker.move_XY(px, py)
                    input("Press Enter when component ready")
                    picker.pick(px, py, pa)
                    picker.place(tx, ty, tang, board_thickness)
                else:
                    #print("moving")
                    picker.move_camera(trayID)
                    #input("Press Enter when camera ready")
                    #print("done")
                    #print("finding components")
                    tray_margin = 1.0 # around tray [mm]
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
                                            picker.place(tx, ty, tang, board_thickness)
                                            fPlaced = True
                                            break
                                if fPlaced == False:
                                    # found components, but no available components
                                    print("no available componet in tray {0:s}".format(trayID))
                                    ask_component_check(trayID)
                                    cmp = picker.find_component(trayID, tray_margin)
                        
picker.move_Z(200)
picker.move_XY(0, 220)
picker.pump_control(False)
picker.light_control(False)

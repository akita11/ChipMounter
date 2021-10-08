import math
import numpy as np
import time
import csv
import sys
import picker
import operator

args = sys.argv
if len(args) > 1:
    filename = args[1]
else:
    filename = 'paste.csv'

# upper-left corenr of PCB
x0, y0 = (0.0, 0.0)

# PCB size
sx, sy = (99.06, 88.9)

# PCB left-side corner on Base
bx0, by0 = (0, 200)

head_offset = (37.5, -1.5)
board_offset = (90, 0)

# specify target area on PCB (-1 if no specify)
xmin = -1
xmax = 45
ymin = -1
ymax = -1

# dispenser origin = (52.5, 201.5)

r = csv.reader(open(filename))
n = 0

rows = [[float(row[0]), float(row[1]), float(row[2]), float(row[3])] for row in r]

row_sorted = sorted(rows, key=operator.itemgetter(0)) # sort by 1st (x)

picker.move_Z(150) # initial position

#for row in row_sorted:
for row in rows:
    tx0 = row[0]
    ty0 = row[1]
    sx = row[2]
    sy = row[3]
    area = sx * sy
    if ((xmin != -1 and tx0 >= xmin) or (xmin == -1)) and ((xmax != -1 and tx0 <= xmax) or (xmax == -1)) and ((ymin != -1 and ty0 >= ymin) or (ymin == -1)) and ((ymax != -1 and ty0 <= ymax) or (ymax == -1)):
        tx = tx0 - x0 + bx0 + board_offset[0] - head_offset[0]
        ty = ty0 - y0 + by0 + board_offset[1] - head_offset[1]
        #print(row[0], row[1], tx,ty)
        picker.dispense(tx, ty, area)

picker.move_Z(150)
    

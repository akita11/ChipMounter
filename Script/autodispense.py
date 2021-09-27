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

head_offset = (39, -2)
board_offset = (90, 0)

r = csv.reader(open(filename))
n = 0

rows = [[float(row[0]), float(row[1]), float(row[2]), float(row[3])] for row in r]

row_sorted = sorted(rows, key=operator.itemgetter(0)) # sort by 1st (x)

picker.move_Z(150) # initial position

for row in row_sorted:
    tx = row[0] - x0 + bx0 + board_offset[0] - head_offset[0]
    ty = row[1] - y0 + by0 + board_offset[1] - head_offset[1]
    sx = row[2]
    sy = row[3]
    area = sx * sy
    #print(tx,ty)
    picker.dispense(tx, ty, area)

picker.move_Z(150)
    

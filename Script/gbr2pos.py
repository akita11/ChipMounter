import sys
import math

args = sys.argv
if len(args) > 1:
    filename = args[1]
else:
    print("specify GBR data file'")
    exit()

f = open(filename, 'r')

lines = f.readlines()

state = 0
areaR = {}

for line in lines:
    #print(state, line)
    if state == 0 and line.startswith("%AD"):
        # note: assuming Rectangular aperture ('R')
        lineR = line.replace('%AD', '').replace("R","").replace("C","").replace("X"," ").replace(","," ").replace("*", " ")
        pos = lineR.split(" ")
        if line.find('C') == -1:
            areaR[pos[0]] = [float(pos[1]), float(pos[2])]
        else:
            d = float(pos[1])
            r = d / 2
            A = math.pi * r * r
            a = math.sqrt(A)
            areaR[pos[0]] = [a, a]
    elif state == 0 and line.startswith("D"):
        line = line.replace('*', '').replace("\n", "")
        ap = line.replace("\r", "")
    elif line.startswith("X"):
        line = line.replace('X', ' ').replace("Y"," ").replace("D"," ").replace("*", " ")
        pos = line.split(" ")
        posx = float(pos[1]) / 1000000.0
        posy = float(pos[2]) / 1000000.0
        op = pos[3] #D01=draw, D03=flash
        xsize = areaR[ap][0]
        ysize = areaR[ap][1]
        if op == "03": #D03=flash
            print("{0:.3f},{1:.3f},{2:.3f},{3:.3f},F".format(posx, posy, xsize, ysize))
        elif state == 1 and op == "01":
            x, y = int(pos[1]) / 1000000.0, int(pos[2]) / 1000000.0
            xs, ys, np = xs + x, ys + y, np + 1
            if x < xmin:
                xmin = x
            if x > xmax:
                xmax = x
            if y < ymin:
                ymin = y
            if y > ymax:
                ymax = y
            
    if state == 0 and line.startswith("G36"):
        # start of group
        state = 1
        xs, ys, np = 0, 0, 0
        xmin, ymin = 1e9, 1e9
        xmax, ymax = -1e9, -1e9
    if state == 1 and line.startswith("G37"):
        # end of group
        if np > 0:
            posx, posy = xs / np, ys / np
            xsize, ysize = xmax - xmin, ymax - ymin
            print("{0:.3f},{1:.3f},{2:.3f},{3:.3f},D".format(posx, posy, xsize, ysize))
        state = 0

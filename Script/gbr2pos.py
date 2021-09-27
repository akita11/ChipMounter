import sys

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
    if state == 0 and line.startswith("%AD"):
        # note: assuming Rectangular aperture ('R')
        line = line.replace('%AD', '').replace("R","").replace("X"," ").replace(","," ").replace("*", " ")
        pos = line.split(" ")
        areaR[pos[0]] = [float(pos[1]), float(pos[2])]
    elif state == 0 and line.startswith("D"):
        line = line.replace('*', '').replace("\n", "")
        ap = line
        state = 10
    elif state == 10 and line.startswith("X"):
        line = line.replace('X', ' ').replace("Y"," ").replace("D"," ")
        pos = line.split(" ")
        posx = float(pos[1]) / 1000000.0
        posy = float(pos[2]) / 1000000.0
        xsize = areaR[ap][0]
        ysize = areaR[ap][1]
        print("{0:.3f},{1:.3f},{2:.3f},{3:.3f}".format(posx, posy, xsize, ysize))
        state = 0
    if state == 0 and line.startswith("G36"):
        state = 1
    if state == 1 and line.startswith("G01"):
        state = 2
        xs, ys, np = 0, 0, 0
        xmin, ymin = 1e9, 1e9
        xmax, ymax = -1e9, -1e9
    if state == 2 and line.startswith("X"):
        line = line.replace('X', ' ').replace("Y"," ").replace("D"," ").replace("I", " ")
        pos = line.split(" ")
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
    if state == 2 and line.startswith("G37"):
        if np > 0:
            posx, posy = xs / np, ys / np
            xsize, ysize = xmax - xmin, ymax - ymin
            print("{0:.3f},{1:.3f},{2:.3f},{3:.3f}".format(posx, posy, xsize, ysize))
        state = 0

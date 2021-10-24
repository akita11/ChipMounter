# memo: camera center is located 32.0mm left of pickup center, y=220mm

import json
import cv2
import numpy as np
import math
from socket import *
import time

# physical limit
Xlimit = [0, 240]
Ylimit = [0, 259]
#Zlimit = [0, 160] #[mm]
Zlimit = [0, 800]

#--------------------------------------------------------
global udpSock, UDP_SERIAL_Addr
# local client
Client_IP = "127.0.0.1"
Client_Port = 10031
Client_Addr = (Client_IP, Client_Port)
# UDP-Serial server 
UDP_SERIAL_IP = "127.0.0.1"
UDP_SERIAL_Port = 10030
UDP_SERIAL_Addr = (UDP_SERIAL_IP, UDP_SERIAL_Port)
udpSock = socket(AF_INET, SOCK_DGRAM)
udpSock.bind(Client_Addr)
udpSock.settimeout(1)

cap = ""
Ncap = 0

A2image = {}
A2real = {}

def load_config(filename = 'config.txt') :
#def load_config(filename) :
    global config, pos_r, pos_c, pos_r_o, pos_c_o, pos_r_e, pos_c_e, cap
    print("Loading "+filename)
    config = json.load(open(filename, 'r'))

    camID = config["Camera"]["ID"]
    cap = cv2.VideoCapture(camID, cv2.CAP_DSHOW)
    print("capture size: ({0:d}, {1:d})".format(config["Camera"]["Pixel"][0], config["Camera"]["Pixel"][1]))
    #cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'));
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  config["Camera"]["Pixel"][0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config["Camera"]["Pixel"][1])

    for trayID in config["Tray"]:
        A2image[trayID] = calc_transform_to_image(trayID).tolist()
        A2real[trayID] = calc_transform_to_real(trayID).tolist()
        #print(trayID, A2image[trayID])
        #print(trayID, A2real[trayID])

    return config

def save_config(data, filename = 'config.txt'):
    print("Saving "+filename)
    json.dump(data, open(filename, 'w'))

def send_cmd(cmd):
    global udpSock, UDP_SERIAL_Addr
    udpSock.sendto(cmd.encode('utf-8'), UDP_SERIAL_Addr)
    UDP_BUFSIZE = 1024
    #data, addr = udpSock.recvfrom(UDP_BUFSIZE)
    #print(data)
    '''
    while True:
        try:
            data, addr = udpSock.recvfrom(UDP_BUFSIZE)
        except:
            print("timeout")
        else:
            print("*",data)
            break;
    '''
    while True:
        try:
            data, addr = udpSock.recvfrom(UDP_BUFSIZE)
        except:
            #print("timeout")
            pass
        else:
            #print("*",data)
            break;

def capture(fCapture, trayID, fWarp = False):
    global cap,Ncap
    if fCapture == True:
        ret,img_src = cap.read()
        ret,img_src = cap.read()
        ret,img_src = cap.read()
        cv2.imwrite('raw{0:d}.png'.format(Ncap), img_src)
        Ncap = Ncap + 1
    else:
        img_src = cv2.imread('raw.png', 1)
    if (fWarp == True):
        # perform warp perspective
        #img_src = cv2.warpPerspective(img_src, np.array(config["Tray"][trayID]["MatrixToImage"]), config["Camera"]["Pixel"])
        img_src = cv2.warpPerspective(img_src, np.array(A2image[trayID]), config["Camera"]["Pixel"])

    return(img_src)

def move_XY(x, y):
    if (Xlimit[0] <= x <= Xlimit[1]) and (Ylimit[0] <= y <= Ylimit[1]):
        send_cmd('G0X{:.2f}Y{:.2f}'.format(x, y))
    else:
        print("X={0:.2f} is out of range ({1:.1f}, {2:.1f})".format(x, Ylimit[0], Ylimit[1]))
        print("Y={0:.2f} is out of range ({1:.1f}, {2:.1f})".format(y, Ylimit[0], Ylimit[1]))


def move_X(pos):
    if Xlimit[0] <= pos <= Xlimit[1]:
        send_cmd('G0X{:.2f}'.format(pos))
    else:
        print("X={0:.2f} is out of range ({1:.1f}, {2:.1f})".format(pos, Ylimit[0], Ylimit[1]))

def move_Y(pos):
    if Ylimit[0] <= pos <= Ylimit[1]:
        send_cmd('G0Y{:.2f}'.format(pos))
    else:
        print("Y={0:.2f} is out of range ({1:.1f}, {2:.1f})".format(pos, Ylimit[0], Ylimit[1]))

def move_Z(pos):
#    pos = pos * 5 # Z's [step/mm] = XY's [step/mm] * 5
    if Zlimit[0] <= pos <= Zlimit[1]:
        send_cmd('G0Z{:.2f}'.format(pos))

def intake_control(status):
    if (status == True):
        send_cmd('M3')
    else:
        send_cmd('M5')

def exhaust_control(status):
    if (status == True):
        send_cmd('M7')
    else:
        send_cmd('M9')

def rotate_head(angle):
    send_cmd('G0A'+'{:.2f}'.format(angle * 100 / 360))

theta_s = -180
theta_range = 360
def normalize_angle(theta):
    # normalize [theta_s:theta_e]
    theta_e = theta_s + theta_range
    while theta < theta_s:
        theta = theta + theta_range
    while theta > theta_e:
        theta = theta - theta_range
    return theta

# calculate minimzed rotation
def angle_to_horizontal(theta):
    theta = normalize_angle(theta)
    if theta_s/2 < theta < (theta_s + theta_range)/2: 
        rot = -theta
    else:
       rot = -theta + theta_range/2
    return normalize_angle(rot)
    
def pick(x, y, angle):
    print("pick ({0:.2f}, {1:.2f} / {2:.2f})".format(x, y, angle))
    move_Z(config["Physical"]["Height"]["Motion"])
    #move_Z(config["Camera"]["Height"])
    move_XY(x, y)
    move_Z(config["Physical"]["Height"]["Pick"])
    intake_control(True)
    time.sleep(0.2)
    move_Z(config["Physical"]["Height"]["Motion"])
    rotate_head(angle_to_horizontal(angle))
    ## ToDo: wait for head rotate finished

def place(x, y, angle, thickness):
    print("place ({0:.2f}, {1:.2f} / {2:.2f})".format(x, y, angle))
    move_XY(x, y)
    #rotate_head(angle)
    rotate_head(angle_to_horizontal(angle))
    ## ToDo: wait for head rotate finished
    #print("place angle=",angle)
    move_Z(config["Physical"]["Height"]["Place"] + thickness * 5)
    intake_control(False)
    exhaust_control(True)
    #time.sleep(0.2)
    time.sleep(0.5)
    exhaust_control(False)
    move_Z(config["Physical"]["Height"]["Motion"])
    #move_Z(config["Camera"]["Height"])

def digitize(img, HSV_Range):
    # convert H=(0:180) to (0:360), S&V=(0:100) to (0:255)
    hsvL = np.array([HSV_Range["Lower"]["H"] / 2,
                     HSV_Range["Lower"]["S"] / 100.0 * 255,
                     HSV_Range["Lower"]["V"] / 100.0 * 255])
    hsvU = np.array([HSV_Range["Upper"]["H"] / 2,
                     HSV_Range["Upper"]["S"] / 100.0 * 255,
                     HSV_Range["Upper"]["V"] / 100.0 * 255])
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    img_bin = cv2.inRange(img_hsv, hsvL, hsvU)
    return(img_bin)

def calc_transform(pos_from, pos_to, fMoveOrigin = True):
    # temporal origin
    if (fMoveOrigin == True):
        pos_from_o = [(pos_from[0][0]+pos_from[1][0]+pos_from[2][0]+pos_from[3][0])/4,
                      (pos_from[0][1]+pos_from[1][1]+pos_from[2][1]+pos_from[3][1])/4]
        pos_to_o   = [(pos_to[0][0]+pos_to[1][0]+pos_to[2][0]+pos_to[3][0])/4,
                      (pos_to[0][1]+pos_to[1][1]+pos_to[2][1]+pos_to[3][1])/4]
    else:
        pos_from_o = [0, 0]
        pos_to_o   = [0, 0]
    # 4 corner of colored area in camera image
    pos_from_e= [np.array([pos_from[0][0] - pos_from_o[0], pos_from[0][1] - pos_from_o[1]]),
                 np.array([pos_from[1][0] - pos_from_o[0], pos_from[1][1] - pos_from_o[1]]),
                 np.array([pos_from[2][0] - pos_from_o[0], pos_from[2][1] - pos_from_o[1]]),
                 np.array([pos_from[3][0] - pos_from_o[0], pos_from[3][1] - pos_from_o[1]])]
    pos_to_e= [np.array([pos_to[0][0] - pos_to_o[0], pos_to[0][1] - pos_to_o[1]]),
               np.array([pos_to[1][0] - pos_to_o[0], pos_to[1][1] - pos_to_o[1]]),
               np.array([pos_to[2][0] - pos_to_o[0], pos_to[2][1] - pos_to_o[1]]),
               np.array([pos_to[3][0] - pos_to_o[0], pos_to[3][1] - pos_to_o[1]])]
    Aconv = cv2.getPerspectiveTransform(
        np.array([pos_from_e[0], pos_from_e[1], pos_from_e[2], pos_from_e[3]], dtype=np.float32),
        np.array([pos_to_e[0], pos_to_e[1], pos_to_e[2], pos_to_e[3]], dtype=np.float32)
    )
    return Aconv

def calc_transform_to_real(trayID):
    # image -> real
    width, height = config["Camera"]["Pixel"]
    return calc_transform(
        [
            [    0,      0], #'UpperLeft'], 
            [width,      0], #'UpperRight'], 
            [width, height], #'LowerRight'], 
            [    0, height]  #['LowerLeft']
        ],
        [config["Tray"][trayID]['Corner']['Real']['UpperLeft'], 
         config["Tray"][trayID]['Corner']['Real']['UpperRight'], 
         config["Tray"][trayID]['Corner']['Real']['LowerRight'], 
         config["Tray"][trayID]['Corner']['Real']['LowerLeft']],
        True)
    
def calc_transform_to_image(trayID):
    # camera -> image
    width, height = config["Camera"]["Pixel"]
    return calc_transform(
        # 4 corner of colored area in camera
        # camera is mounted with 180 deg rotated
        [config["Tray"][trayID]['Corner']['Camera']['LowerRight'], 
         config["Tray"][trayID]['Corner']['Camera']['LowerLeft'],
         config["Tray"][trayID]['Corner']['Camera']['UpperLeft'], 
         config["Tray"][trayID]['Corner']['Camera']['UpperRight']
         ],
        [
            [    0,      0], #'UpperLeft'], 
            [width,      0], #'UpperRight'], 
            [width, height], #'LowerRight'], 
            [    0, height]  #['LowerLeft']
        ],
        False)

def pos_transform_to(Aconv, pos, pos_from_o, pos_to_o):
    px = pos[0] - pos_from_o[0]
    py = pos[1] - pos_from_o[1]
    prx, pry, w = np.dot(Aconv, [px, py, 1])
    # move temporal origin to origin
    prx = prx + pos_to_o[0]
    pry = pry + pos_to_o[1]
    return [prx, pry]
                          
def pos_transform_to_real(trayID, pos):
    # image -> real
    width, height = config["Camera"]["Pixel"]
    #return pos_transform_to(config["Tray"][trayID]["MatrixToReal"], pos,
    return pos_transform_to(A2real[trayID], pos,
                            [width/2, height/2],
                            [(config["Tray"][trayID]['Corner']['Real']['UpperLeft'][0] +
                              config["Tray"][trayID]['Corner']['Real']['UpperRight'][0] +
                              config["Tray"][trayID]['Corner']['Real']['LowerRight'][0] +
                              config["Tray"][trayID]['Corner']['Real']['LowerLeft'][0])/4,
                             (config["Tray"][trayID]['Corner']['Real']['UpperLeft'][1] +
                              config["Tray"][trayID]['Corner']['Real']['UpperRight'][1] +
                              config["Tray"][trayID]['Corner']['Real']['LowerRight'][1] +
                              config["Tray"][trayID]['Corner']['Real']['LowerLeft'][1])/4
                             ])
                           
def pos_transform_to_image(trayID, pos):
    # camera -> image
    width, height = config["Camera"]["Pixel"]
    #return pos_transform_to(config["Tray"][trayID]["MatrixToImage"], pos,
    return pos_transform_to(A2image[trayID], pos,
                            [0, 0], [0, 0])

def move_camera(tray):
    move_Z(config["Camera"]["Height"])
    # move to camera position
    p = config["Tray"][tray]['Camera']
    move_XY(p[0], p[1])

def light_control(status):
    if status == True:
        send_cmd('M12')
    else:
        send_cmd('M13')

def pump_control(status):
    if status == True:
        send_cmd('M10')
    else:
        send_cmd('M11')

def find_component(trayID, margin=0):
    #    move_camera(trayID)
    #    img = capture(True, config['Camera']['ID'], trayID)
    img = capture(True, config['Camera']['ID'], trayID)
    cmp, img_ext = create_component_list(img, trayID, margin)
    #cv2.imwrite('ext{0:d}.png'.format(Ncap), img_ext)
    return(cmp)
    
    
def create_component_list(img, trayID, tray_margin = 0):
    #img_rect = cv2.warpPerspective(img, np.array(config["Tray"][trayID]["MatrixToImage"]), config["Camera"]["Pixel"])
    img_rect = cv2.warpPerspective(img, np.array(A2image[trayID]), config["Camera"]["Pixel"])
    areaL, areaU = config["Tray"][trayID]["Area"]["Component"]["Lower"], config["Tray"][trayID]["Area"]["Component"]["Upper"]
    # area threshold for black area
    areaLB, areaUB = config["Tray"][trayID]["Area"]["Black"]["Lower"], config["Tray"][trayID]["Area"]["Black"]["Upper"] 
    height, width, channel = img.shape
    img_mask = 255 - digitize(img_rect, config["HSV_Range"]["Back"])
    #cv2.imwrite('mask{0:d}.png'.format(Ncap), img_mask)
    img_ext = cv2.bitwise_and(img_rect, img_rect, mask=img_mask)
    #cv2.imwrite('ext_{0:d}.png'.format(Ncap), img_ext)
    img_maskB = digitize(img_rect, config["HSV_Range"]["Black"])
    img_black = cv2.bitwise_and(img_mask, img_maskB)
    #--------------------------------------
    # labeling of digitized image
    #--------------------------------------
    nlabels, labels, stats, centroids = cv2.connectedComponentsWithStats(img_mask)
    img_label = np.zeros((height, width), dtype = 'uint8')

    for i in range(1, nlabels):
        if stats[i][4] > 200:
            cv2.putText(img_ext, '{:d}'.format(stats[i][4]), (int(centroids[i][0]), int(centroids[i][1])), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        if areaL < stats[i][4] < areaU: # object's size
            img_label[labels == i] = 255
    # detecting black area (front of R)
    nlabelsB, labelsB, statsB, centroidsB = cv2.connectedComponentsWithStats(img_maskB)
    img_labelB = np.zeros((height, width), dtype = 'uint8')

    for i in range(1, nlabelsB):
        if statsB[i][4] > 100:
            cv2.putText(img_ext, '{:d}'.format(statsB[i][4]), (int(centroidsB[i][0]), int(centroidsB[i][1])+50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 1, cv2.LINE_AA)
        if areaLB < statsB[i][4] < areaUB: # object's size
            img_labelB[labelsB == i] = 255
        
    contours, hierarchy = cv2.findContours(img_label, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
    #--------------------------------------
    # store component positions
    #--------------------------------------
    tray_p1 = config["Tray"][trayID]["Corner"]["Real"]["UpperLeft"]
    tray_p2 = config["Tray"][trayID]["Corner"]["Real"]["UpperRight"]
    tray_p3 = config["Tray"][trayID]["Corner"]["Real"]["LowerRight"]
    tray_p4 = config["Tray"][trayID]["Corner"]["Real"]["LowerLeft"]
    tray_xs, tray_xe = (tray_p1[0] + tray_p4[0]) / 2, (tray_p2[0] + tray_p3[0]) / 2
    tray_ys, tray_ye = (tray_p3[1] + tray_p4[1]) / 2, (tray_p1[1] + tray_p2[1]) / 2
    
    cmp = []
    for i, cnt in enumerate(contours):
        rect = cv2.minAreaRect(cnt)
        px = rect[0][0]
        py = rect[0][1]
    
        ang = rect[2] / 180 * math.pi # deg -> rad
        box_int = np.int0(cv2.boxPoints(rect))
        box = cv2.boxPoints(rect)
        
        ba1 = (box[0] + box[1])/2
        ba2 = (box[2] + box[3])/2
        bb1 = (box[0] + box[3])/2
        bb2 = (box[1] + box[2])/2
        la = np.linalg.norm(ba1 - ba2)
        lb = np.linalg.norm(bb1 - bb2)
        if la < lb:
            ang = ang + math.pi/2
        angD = ang / math.pi * 180 # angle in degree
        angR = angD / 360 * 100 # angle in percent
            
        # find front side (black area)
        x1 = px
        y1 = py
        fFront = False;
        for j in range(1, nlabelsB):
            if areaLB < statsB[j][4] < areaUB: # object's size
                x2 = centroidsB[j][0]
                y2 = centroidsB[j][1]
                d = np.array([x2 - x1, y2 - y1])
                dis = np.linalg.norm(d)
                if dis < 5:
                    fFront = True
        cv2.drawContours(img_ext, [box_int], 0, (0,0,255), 1)

        rl = 10
        rs = 5
        p1x = np.int0(px + rl * math.cos(ang))
        p1y = np.int0(py + rl * math.sin(ang))
        p2x = np.int0(px - rl * math.cos(ang))
        p2y = np.int0(py - rl * math.sin(ang))
        p3x = np.int0(px + rs * math.cos(ang+math.pi/2))
        p3y = np.int0(py + rs * math.sin(ang+math.pi/2))
        p4x = np.int0(px - rs * math.cos(ang+math.pi/2))
        p4y = np.int0(py - rs * math.sin(ang+math.pi/2))
        cv2.line(img_ext, (p1x, p1y), (p2x, p2y), (0, 255, 0))
        cv2.line(img_ext, (p3x, p3y), (p4x, p4y), (0, 0, 255))
        if fFront == True:
            cv2.circle(img_ext, (int(px), int(py)), 20, (255, 255, 255))

        prx, pry = pos_transform_to_real(trayID, [px, py])
        # store in compnent list in each tray
        #print(prx, pry, tray_xs, tray_xe, tray_ys, tray_ye, tray_margin)
        if tray_xs + tray_margin <= prx <= tray_xe - tray_margin and tray_ys + tray_margin <= pry <= tray_ye - tray_margin:
            cmp.append([prx, pry, angD, fFront])
        
    return(cmp, img_ext)

def move_dispense(d):
    send_cmd('G0B{:.2f}'.format(d))

Aextrude = 2                    # coefficient of extrude per area[mm2]
Aback = 0.8

Zoffset_extrude = 1 # 1/5=0.2mm

def dispense(x, y, area, Zoffset, thickness):
    # dispense solder at (x, y), pad area of "area"
    extrude = area * Aextrude
    back = area * Aback
    print("solder paste at ({0:.3f}, {1:.3f}), area={2:.3f} / extrude={3:.3f}".format(x, y, area, extrude))
    move_XY(x, y)
    move_Z(Zoffset + thickness * 5 + Zoffset_extrude)
    move_dispense(extrude)
    move_dispense(-back)
    move_Z(Zoffset + thickness * 5 + 10 + Zoffset_extrude)

def load_board_config(filename = 'board.txt') :
    print("Loading board config from "+filename)
    board = json.load(open(filename, 'r'))
    return board

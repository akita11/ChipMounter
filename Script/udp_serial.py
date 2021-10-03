from socket import *
import serial
import time

#fNoSerial = True
fNoSerial = False

# UDP-Serial server
UDP_SERIAL_IP = "127.0.0.1"
UDP_SERIAL_Port = 10030

if fNoSerial == True:
    print("***Debug mode without serial***")

#----------------------------------
UDP_SERIAL_Addr = (UDP_SERIAL_IP, UDP_SERIAL_Port)
BUFSIZE = 1024

udpSock = socket(AF_INET, SOCK_DGRAM)
udpSock.bind(UDP_SERIAL_Addr)
udpSock.settimeout(1)

def wait_motion():
    if fNoSerial == False:
        finish = False
        count = 0
        #while finish == False:
        while count < 2: # check 2 times of "IDLE" to avoid incorrect motion end detection
            ser.write(b'@\n')
            line = "init"
            #while finish == False and len(line) != 0:
            while count < 2 and len(line) != 0:
                #line = ser.readline().decode()
                line0 = ser.readline()
                try:
                    # to skip "garbage" binary
                    line = line0.decode()
                except:
                    pass
                else:
                    finish = 'IDLE' in line
                    if finish == True:
                        count = count + 1
                    time.sleep(0.01)
    print("-> done")
    return


def send_cmd(cmd):
    if fNoSerial == False:
        cmd = cmd + '\n'
        s = cmd.encode()
        ser.write(s)
        if s[0] == 77: # 'M'
            #time.sleep(0.2)
            time.sleep(0.01)
        else:    
            wait_motion()

print("Homing...")
if fNoSerial == False:
    ser = serial.Serial('COM5',115200,timeout=0.1)

time.sleep(1)
send_cmd('$H')
send_cmd('G0Z80')

print("Ready")
while True:                                     
    try:
        data, addr = udpSock.recvfrom(BUFSIZE)
    except:
        pass
    else:
        print("*"+data.decode())
        send_cmd(data.decode())
        udpSock.sendto("ok".encode('utf-8'), addr)
        if data.decode() == "finish":
            break;
        
print("finish")
if fNoSerial == False:
    ser.close()

#include <M5Stack.h>
#include "GrblControl.h"

#define I2C_ADDR0 0x70 // default address (1st)
#define I2C_ADDR1 0x71 // alternative address (2nd)

#define SOL_A 26
#define SOL_B 12
#define SOL_C 13
#define SOL_D 5

GRBL _GRBL0 = GRBL(I2C_ADDR0);
GRBL _GRBL1 = GRBL(I2C_ADDR1);
uint8_t fGRBL = 1;

#define LEDC_CHANNEL_0 0
#define LEDC_TIMER_BIT 8
#define LEDC_BASE_FREQ 2400.0
#define TDS_CLK_PIN SOL_C
#define SOLC_ON_DUTY  0x80 // 50%
#define SOLC_OFF_DUTY 0x00 // 0%

void setup() {
  M5.begin();
  M5.Power.begin();
  //void GRBL::Init(uint32_t x_step,uint32_t y_step,uint32_t z_step,uint32_t acc)
  // $0: #define DEFAULT_X_STEPS_PER_MM 250.0
  // $1: #define DEFAULT_Y_STEPS_PER_MM 250.0
  // $2: #define DEFAULT_Z_STEPS_PER_MM 250.0
  // $8: #define DEFAULT_ACCELERATION (10.0*60*60) // 10 mm/min^2

  // motor   : 1.8deg/step = 200step / rotate
  // gear    :  20 mount / rorate
  // X/Y belt:  1 mount = 2 mm
  // Z screw :  8mm / rotate
  // -> XY: 10 step = 1 mount = 2mm, 5step / mm
  //    Z : 200step = 8mm            25step / mm

  // -> XY: 10 step = 1 mount = 1mm, 10step / mm
  //    Z : 200step = 2mm            100step / mm
  //#define XY_STEP_PER_MM 5 // 1mm(cmd) -> 2mm(actual)
  //#define Z_STEP_PER_MM 25 // 1mm(cmd) -> 4mm(actual)
  //#define ACC 20 // acc is converted *(60*60) in M5-GRBL
#define XY_STEP_PER_MM 160 // 1mm(cmd) -> 2mm(actual), 1/32 microstep
  //#define Z_STEP_PER_MM 800 // 1mm(cmd) -> 4mm(actual), 1/32 microstep
#define Z_STEP_PER_MM 160 // 1mm(cmd) -> 4mm(actual), 1/32 microstep, 1/5
#define ACC 500 // acc is converted *(60*60) in M5-GRBL, 1/32 microstep

// A-axis (pick-up head) motor: 6400step/rotaate
// $1=64, $5=10000 -> 100mm=1rotate 

  //  _GRBL0.Init(XY_STEP_PER_MM, XY_STEP_PER_MM, Z_STEP_PER_MM, ACC);
  //  _GRBL1.Init(XY_STEP_PER_MM, XY_STEP_PER_MM, Z_STEP_PER_MM, ACC);
  _GRBL0.Init();;
  _GRBL1.Init();;
  _GRBL1.Gcode("G91"); // relative mode for GRBL1

  /*
    _GRBL0.Gcode("$0=160");
    _GRBL0.Gcode("$1=160");
    _GRBL0.Gcode("$2=800");
    _GRBL0.Gcode("$3=30");
    _GRBL0.Gcode("$4=800"); // default feed rate (for G1)
    _GRBL0.Gcode("$5=800"); // default seek rate (for G0 -> 3000)
    _GRBL0.Gcode("$6=96"); // invert X&Y axis
    _GRBL0.Gcode("$8=50"); // acc
    _GRBL0.Gcode("$16=0"); // disable hard liit
    _GRBL0.Gcode("$17=1"); // enable homing at boot
    _GRBL0.Gcode("$18=224"); // invert X/Y/Z homing direction
    _GRBL0.Gcode("$19=800"); // homing feed rate
    _GRBL0.Gcode("$20=800"); // homing seek rate -> 3000
    _GRBL0.Gcode("$22=0"); // disable homing pulloff
  */

  pinMode(SOL_A, OUTPUT); digitalWrite(SOL_A, 0);
  pinMode(SOL_B, OUTPUT); digitalWrite(SOL_B, 0);
//  pinMode(SOL_C, OUTPUT); digitalWrite(SOL_C, 0);
  pinMode(SOL_D, OUTPUT); digitalWrite(SOL_D, 0);
  Serial.begin(115200);
  m5.Lcd.setTextColor(WHITE, BLACK);
  m5.Lcd.setTextSize(3);
  m5.Lcd.setBrightness(100);
  M5.Lcd.setCursor(80, 20);
  M5.Lcd.println("GRBL13.2");
  M5.Lcd.setCursor(80, 60);
  M5.Lcd.println("<-> Serial");
  M5.Lcd.setCursor(40, 160);
  M5.Lcd.println("Solenoid");

  ledcSetup(LEDC_CHANNEL_0, LEDC_BASE_FREQ, LEDC_TIMER_BIT);
  ledcAttachPin(TDS_CLK_PIN, LEDC_CHANNEL_0);
  ledcWrite(LEDC_CHANNEL_0, 0x00);

  SolenoidStatus(0, 0);
  SolenoidStatus(1, 0);
  SolenoidStatus(2, 0);
  SolenoidStatus(3, 0);
  while (Serial.available()) Serial.read(); // force serial buffer empty
  ReadGRBLstatus(0);
  ReadGRBLstatus(1);
  Serial.println("ready");
}

void SolenoidStatus(int ch, int status)
{
  fGRBL = 0;
  m5.Lcd.setTextSize(3);
  if (ch == 0) {
    if (status == 1) {
      m5.Lcd.setTextColor(RED, BLACK);
      digitalWrite(SOL_A, 1);
    }
    else {
      m5.Lcd.setTextColor(WHITE, BLACK);
      digitalWrite(SOL_A, 0);
    }
    M5.Lcd.setCursor(60, 200);
    M5.Lcd.println("A");
  }
  else if (ch == 1) {
    if (status == 1) {
      m5.Lcd.setTextColor(RED, BLACK);
      digitalWrite(SOL_B, 1);
    }
    else {
      m5.Lcd.setTextColor(WHITE, BLACK);
      digitalWrite(SOL_B, 0);
    }
    M5.Lcd.setCursor(150, 200);
    M5.Lcd.println("B");
  }
  else if (ch == 2){
    if (status == 1) {
      m5.Lcd.setTextColor(RED, BLACK);
      ledcWrite(LEDC_CHANNEL_0, SOLC_ON_DUTY);
//      digitalWrite(SOL_C, 1);
    }
    else {
      m5.Lcd.setTextColor(WHITE, BLACK);
      ledcWrite(LEDC_CHANNEL_0, SOLC_OFF_DUTY);
//      digitalWrite(SOL_C, 0);
    }
    M5.Lcd.setCursor(240, 200);
    M5.Lcd.println("C");
  }
  else if (ch == 3){
    if (status == 1) {
      m5.Lcd.setTextColor(RED, BLACK);
      digitalWrite(SOL_D, 1);
    }
    else {
      m5.Lcd.setTextColor(WHITE, BLACK);
      digitalWrite(SOL_D, 0);
    }
    M5.Lcd.setCursor(280, 200);
    M5.Lcd.println("D");
  }
}

void ReadGRBLstatus(int ch) {
  String s;
  if (ch == 0) s = _GRBL0.ReadLine();
  // else s = _GRBL1.ReadLine(); // ignore GRBL1's response
  //  Serial.print(s.length()); Serial.print('<');
  Serial.print(s);
  //  Serial.println('>');
}

int pos = 0;
char buf[1024];
int fSolCD = 0;

void loop() {
  char c;
  int ch, i;
  M5.update();
  if (M5.BtnA.wasPressed()) {
    SolenoidStatus(0, 1);
  } else if (M5.BtnA.wasReleased()) {
    SolenoidStatus(0, 0);
  }
  if (M5.BtnB.wasPressed()) {
    SolenoidStatus(1, 1);
  } else if (M5.BtnB.wasReleased()) {
    SolenoidStatus(1, 0);
  }

  if (M5.BtnC.wasPressed()) {
    // toggle Solenoid-C
    fSolCD = (fSolCD + 1) % 4;
    if ((fSolCD & 0x01) == 0) SolenoidStatus(2, 0); else SolenoidStatus(2, 1);
    if ((fSolCD & 0x02) == 0) SolenoidStatus(3, 0); else SolenoidStatus(3, 1);
  } else if (M5.BtnC.wasReleased()) {
  }

  while (Serial.available()) {
    c = Serial.read();
    if (c == '\r' || c == '\n') {
      buf[pos] = '\0';
      if (pos > 0 && (buf[pos - 1] == '\r' || buf[pos - 1] == '\n')) buf[pos - 1] = '\0';
      if (pos != 0) {
        Serial.print('['); Serial.print(buf); Serial.println(']');
      }
      fGRBL = 1;
      if (buf[0] == 'M') {
        if (buf[1] == '3') SolenoidStatus(0, 1);      // M3:Solnenoid A on
        else if (buf[1] == '5') SolenoidStatus(0, 0); // M5:Solnenoid A off
        else if (buf[1] == '7') SolenoidStatus(1, 1); // M7:Solnenoid B on
        else if (buf[1] == '9') SolenoidStatus(1, 0); // M9:Solnenoid B off
        else if (buf[1] == '1' && buf[2] == '0')
          SolenoidStatus(2, 1); // M10: Solnenoid C on
        else if (buf[1] == '1' && buf[2] == '1')
          SolenoidStatus(2, 0); // M11: Solnenoid C off
        else if (buf[1] == '1' && buf[2] == '2')
          SolenoidStatus(3, 1); // M12: Solnenoid D on
        else if (buf[1] == '1' && buf[2] == '3')
          SolenoidStatus(3, 0); // M13: Solnenoid D off
      }
      if (fGRBL == 1) {
        ch = 0;
        // A/B/C axis -> GRBL1's X/Y/Z axis
        for (i = 0; i < pos; i++) {
          if (buf[i] == 'A') {
            ch = 1;
            buf[i] = 'X';
          }
          if (buf[i] == 'B') {
            ch = 1;
            buf[i] = 'Y';
          }
          if (buf[i] == 'C') {
            ch = 1;
            buf[i] = 'Z';
          }
        }
        Serial.print(ch); Serial.print(' '); Serial.println(buf);        
        if (ch == 0) {
          _GRBL0.Gcode(buf);
          ReadGRBLstatus(0);
        }
        else {
          _GRBL1.Gcode(buf);
          ReadGRBLstatus(1);
        }
      }
      pos = 0;
    }
    else buf[pos++] = c;
  }
}

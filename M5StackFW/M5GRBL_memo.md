# M5StackのGRBLユニットのドキュメントの補足

## 内部変数 / Internal variables

[M5StackのGRBL](https://docs.m5stack.com/en/module/grbl13.2)の$で指定する内部変数は、ドキュメントに記載されている情報と異なる。ソースコードを読んだ結果から、以下が正しい（ドキュメントから変更があるもののみ記載）なお各変数の値は、設定を変更すると自動でEEPROMに保存される。どうも挙動が怪しいときは、何かのミスで変数を別の値に設定してしまっていないか確認するとよい。

Internal variables of [M5StackのGRBL](https://docs.m5stack.com/en/module/grbl13.2), which is automatically saved into EEPROM. Some in its document are incorrect, the followings are correct ones analyzed from its source code.


- $6 : step port invert mask. binary = 0 (<-- $7 in document)
- $10 : settings.mm_per_arc_segment = value;
- $11 : settings.n_arc_correction = round(value);
- $12 : settings.decimal_places = round(value);
- $13 : REPORT_INCHES
- $14 : BITFLAG_AUTO_START(=1)
- $15 : invert ST(=0)
- $16 : enable hard limit
- $17 : enable homing
- $18 : settings.homing_dir_mask = trunc(value);
- $19 : settings.homing_feed_rate = value;
- $20 : settings.homing_seek_rate = value;
- $21 : settings.homing_debounce_delay = round(value);
- $22 : settings.homing_pulloff = value;

## 内部変数の補足

- $6 (step port invert mask): X,Y,Z軸の正の向きを反転させる指定。config.hに各軸のビットが指定されているので、1をこれだけビットシフトしたものの論理和として指定する。例えばX,Z軸を反転させるなら、1<<5=32(0x20)と1<<7=128(0x80)の論理和である160(0xa0)とすればよい。
```
#define X_DIRECTION_BIT    5  // Uno Digital Pin 5
#define Y_DIRECTION_BIT    6  // Uno Digital Pin 6
#define Z_DIRECTION_BIT    7  // Uno Digital Pin 7
```

- $15 (invert ST): これを1にすると、モータの動作／停止が逆になる。（何に使うのかよくわからない）
- $17 (enable homing): これが1だと、初期化時のホーミング（原点復帰）を必須、つまり、リセット後にまずは$Hコマンドでホーミングを行わないと、他の動作はできない。

- $18 (settings.homing_dir_mask): $6と同様に、ホーミング動作の向きを指定する。一般には各軸の正の向きとホーミングの向きは逆なので、各軸を反転させることになる。

## 各軸の速度 ($4や$5など)

本来は各軸で同じになるはずだが、$0-$2で各軸のstep/mmが異なるとき、各軸が違う速度になる気がする（速度を大きな値、step/mmを大きな値にすると、脱調する）。ソースコードを読んでも、原因はよくわからず。

## I2Cバッファ

M5Stack GRBLとM5Stackとの通信はI2C。マスタ(M5Stack)からI2C読み出しを行うと、その時点でバッファにたまっているメッセージを読み出せる。ただしバッファのサイズが10バイトしかなく、$$のような長過ぎるメッセージは、文字化け（バッファの上書き）する。

なお、GRBLのライブラリ中のGrblControl.cpp の ReadStatus() は、でdataの末尾に'\0'が付加されないのはたぶんバグなので、以下のように修正すべき。
ReadStatus() in GrblControl.cpp should be corrected as follows to add terminator of '\0' at end of data.
```
String GRBL::ReadLine() {
    String Data = ""; 
    while(1){
        uint8_t i = 0;
        char data[11];
        Wire.requestFrom(addr, 10);
        while (Wire.available() > 0) {
            data[i] = Wire.read();
            i++;
        }
        data[i] = '\0';
        Data += data;
        if (data[9] == 0xff) {
            break;
        }
    }
    return Data;
}
```
## Gコード・GRBLの一般的な情報

- https://bbs.avalontech.jp/t/grbl-g/750/3
- http://ichirowo.com/2016/09/cnc_grbl/

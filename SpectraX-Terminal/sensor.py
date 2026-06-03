# sensor.py
import serial

class RFReceiver:
    def __init__(self, port, baud_rate):
        self.ser = None
        try:
            self.ser = serial.Serial(port, baud_rate, timeout=0.05)
            print(f"[BAŞARILI] Donanım {port} hattına bağlandı.")
        except Exception:
            print(f"[HATA] {port} açılamadı. Sistem verisiz başlatılıyor.")

    def read_latest_data(self):
        if not self.ser or self.ser.in_waiting == 0:
            return None, None

        last_valid_line = None
        try:
            lines = self.ser.readlines()
            for line in reversed(lines):
                decoded = line.decode('utf-8', errors='ignore').strip()
                if "RSSI:" in decoded and ",STATUS:" in decoded:
                    last_valid_line = decoded
                    break
        except Exception:
            pass

        if last_valid_line:
            parts = last_valid_line.split(",")
            rssi_val = int(parts[0].split(":")[1])
            status_str = parts[1].split(":")[1]
            return rssi_val, status_str
            
        return None, None

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            
    
    def send_command(self, cmd_string):
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(cmd_string.encode('utf-8'))
                print(f"[KOMUT GÖNDERİLDİ] -> {cmd_string}")
            except Exception as e:
                print(f"[KOMUT HATASI] Gönderilemedi: {e}")
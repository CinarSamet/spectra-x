import numpy as np
import csv
import datetime
import winsound

class ThreatAnalyzer:
    def __init__(self):
        self.total_attacks = 0
        self.max_noise = -120
        self.is_currently_attacked = False

    def analyze(self, rssi_val, status_str, rssi_history):
        attack_type = "Yok"
        
        if rssi_val > self.max_noise:
            self.max_noise = rssi_val

        if status_str == "JAMMING_ATTACK":
            recent_data = list(rssi_history)[-10:] if len(rssi_history) >= 10 else list(rssi_history)
            std_dev = np.std(recent_data) if len(recent_data) > 0 else 0
            
            if std_dev < 3.0:
                attack_type = "Sürekli (CW) Jamming"
            else:
                attack_type = "Paket Yağmuru (Flood)"

            if not self.is_currently_attacked:
                self.total_attacks += 1
                winsound.PlaySound("SystemHand", winsound.SND_ALIAS | winsound.SND_ASYNC)
                self.is_currently_attacked = True
        else:
            self.is_currently_attacked = False

        return attack_type


class DataLogger:
    def __init__(self):
        self.is_recording = False
        self.filename = ""

    def toggle_recording(self):
        self.is_recording = not self.is_recording
        if self.is_recording:
            self.filename = f"frostguard_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            with open(self.filename, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "RSSI_dBm", "Status", "Classification"])
        return self.is_recording

    def log_data(self, rssi, status, attack_type):
        if self.is_recording:
            with open(self.filename, mode='a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
                writer.writerow([timestamp, rssi, status, attack_type])
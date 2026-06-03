import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque
import numpy as np

from config import SERIAL_PORT, BAUD_RATE, MAX_DATA_POINTS, THEME_MODE, THEME_COLOR
from sensor import RFReceiver
from core_logic import ThreatAnalyzer, DataLogger

class SpectraXTerminal(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        ctk.set_appearance_mode(THEME_MODE)
        ctk.set_default_color_theme(THEME_COLOR)
        self.title("SPECTRA-X | Komuta Kontrol Merkezi v4.0 MODÜLER")
        self.geometry("1366x768")
        self.configure(fg_color="#0a0b10")

        self.receiver = RFReceiver(SERIAL_PORT, BAUD_RATE)
        self.analyzer = ThreatAnalyzer()
        self.logger = DataLogger()

        self.time_axis = deque(maxlen=MAX_DATA_POINTS)
        self.rssi_values = deque(maxlen=MAX_DATA_POINTS)
        self.current_time = 0

        self.setup_ui()
        self.update_loop()
        self.is_hopped = False

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=7)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(1, weight=1)

        self.header_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#12141c", border_color="#1f538d", border_width=1)
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        ctk.CTkLabel(self.header_frame, text="🛡️ SPECTRA-X | TACTICAL RF EVASION SYSTEM", font=ctk.CTkFont(family="Consolas", size=24, weight="bold"), text_color="#00d2ff").pack(side="left", padx=20, pady=15)
        
        self.graph_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#12141c", border_color="#2a2d3e", border_width=1)
        self.graph_frame.grid(row=1, column=0, padx=15, pady=15, sticky="nsew")
        
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(8, 6), facecolor='#12141c', gridspec_kw={'height_ratios': [4, 1]})
        self.fig.subplots_adjust(hspace=0.3)

        self.ax1.set_facecolor('#0a0b10')
        self.ax1.tick_params(colors='#888888')
        self.ax1.set_title("SPEKTRUM ANALİZİ", color='#00d2ff', fontsize=11, fontname='Consolas')
        self.ax1.set_ylim(-120, -20)
        self.line, = self.ax1.plot([], [], color="#00d2ff", linewidth=2)
        self.fill = None 

        self.ax2.set_facecolor('#0a0b10')
        self.ax2.axis('off')
        self.waterfall_data = np.full((1, MAX_DATA_POINTS), -120.0)
        self.im = self.ax2.imshow(self.waterfall_data, aspect='auto', cmap='turbo', vmin=-120, vmax=-30)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        self.status_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#12141c", border_color="#2a2d3e", border_width=1)
        self.status_frame.grid(row=1, column=1, padx=(0, 15), pady=15, sticky="nsew")
        
        self.status_box = ctk.CTkFrame(self.status_frame, height=130, corner_radius=10, fg_color="#1a3b1a") 
        self.status_box.pack(pady=20, padx=20, fill="x")
        self.status_box.pack_propagate(False)
        self.status_text = ctk.CTkLabel(self.status_box, text="SİSTEM TEMİZ", font=ctk.CTkFont(family="Consolas", size=24, weight="bold"), text_color="#00ff00")
        self.status_text.pack(expand=True)
        self.sub_status_text = ctk.CTkLabel(self.status_box, text="Tip: Gürültü Yok", font=ctk.CTkFont(family="Consolas", size=14), text_color="white")
        self.sub_status_text.pack(pady=(0, 15))

        self.stats_frame = ctk.CTkFrame(self.status_frame, fg_color="#0a0b10", corner_radius=8)
        self.stats_frame.pack(pady=10, padx=20, fill="x")
        self.rssi_label = ctk.CTkLabel(self.stats_frame, text="Anlık Sinyal: -- dBm", font=ctk.CTkFont(family="Consolas", size=15), text_color="white")
        self.rssi_label.pack(anchor="w", padx=15, pady=(15, 5))
        self.peak_label = ctk.CTkLabel(self.stats_frame, text="Tepe Gürültüsü: -120 dBm", font=ctk.CTkFont(family="Consolas", size=15), text_color="#ffcc00")
        self.peak_label.pack(anchor="w", padx=15, pady=5)
        self.attack_label = ctk.CTkLabel(self.stats_frame, text="Bloke Edilen: 0", font=ctk.CTkFont(family="Consolas", size=15), text_color="#ff5555")
        self.attack_label.pack(anchor="w", padx=15, pady=(5, 15))

        
        self.evasion_btn = ctk.CTkButton(self.status_frame, text="⚡ FREKANS ATLAMA (EVASION MODE)", 
                                         font=ctk.CTkFont(family="Consolas", weight="bold", size=14),
                                         fg_color="#b38f00", hover_color="#cca300", text_color="black",
                                         height=40, command=self.trigger_evasion)
        self.evasion_btn.pack(pady=(20, 10), padx=20, fill="x", side="bottom")

        self.record_btn = ctk.CTkButton(self.status_frame, text="🔴 Veri Kaydını Başlat (CSV)", font=ctk.CTkFont(weight="bold"), 
                                        fg_color="#333333", hover_color="#aa0000", command=self.on_record_btn_click)
        self.record_btn.pack(pady=(0, 20), padx=20, fill="x", side="bottom")

    def on_record_btn_click(self):
        is_recording = self.logger.toggle_recording()
        if is_recording:
            self.record_btn.configure(text="⏹️ Kaydı Durdur", fg_color="#aa0000", hover_color="#ff3333")
        else:
            self.record_btn.configure(text="🔴 Veri Kaydını Başlat (CSV)", fg_color="#333333", hover_color="#555555")

    def update_loop(self):
        rssi_val, status_str = self.receiver.read_latest_data()
        
        if rssi_val is not None:
            self.current_time += 1
            self.time_axis.append(self.current_time)
            self.rssi_values.append(rssi_val)
            
            attack_type = self.analyzer.analyze(rssi_val, status_str, self.rssi_values)
            
            self.logger.log_data(rssi_val, status_str, attack_type)
            
            self.rssi_label.configure(text=f"Anlık Sinyal: {rssi_val} dBm")
            self.peak_label.configure(text=f"Tepe Gürültüsü: {self.analyzer.max_noise} dBm")
            self.attack_label.configure(text=f"Bloke Edilen: {self.analyzer.total_attacks}")
            
            if status_str == "JAMMING_ATTACK":
                self.status_box.configure(fg_color="#3b1a1a")
                self.status_text.configure(text="SİBER SALDIRI!", text_color="#ff3333")
                self.sub_status_text.configure(text=f"Tip: {attack_type}", text_color="#ffcc00")
            else:
                self.status_box.configure(fg_color="#1a3b1a")
                self.status_text.configure(text="SİSTEM TEMİZ", text_color="#00ff00")
                self.sub_status_text.configure(text="Tip: Olağan Gürültü", text_color="white")
                
            self.line.set_data(self.time_axis, self.rssi_values)
            self.ax1.set_xlim(max(0, self.current_time - MAX_DATA_POINTS), self.current_time + 2)
            if self.fill: self.fill.remove()
            self.fill = self.ax1.fill_between(self.time_axis, self.rssi_values, -120, color="#00d2ff", alpha=0.1)
            
            current_len = len(self.rssi_values)
            self.waterfall_data[0, -current_len:] = list(self.rssi_values)
            if current_len < MAX_DATA_POINTS:
                self.waterfall_data[0, :-current_len] = -120
            self.im.set_data(self.waterfall_data)
            
            self.canvas.draw_idle()

        self.after(100, self.update_loop)

    def on_closing(self):
        self.receiver.close()
        self.destroy()
        
    def trigger_evasion(self):
        if not self.is_hopped:
            self.receiver.send_command('HHHHH')
            self.evasion_btn.configure(text="Frekans: 434 MHz (GÜVENLİ KANAL)", fg_color="#2ca02c", text_color="white")
            self.is_hopped = True
        else:
            # 433 MHz'e Geri Dön
            self.receiver.send_command('BBBBB')
            self.evasion_btn.configure(text="⚡ FREKANS ATLAMA (EVASION MODE)", fg_color="#b38f00", text_color="black")
            self.is_hopped = False

if __name__ == "__main__":
    app = SpectraXTerminal()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
#!/usr/bin/env python3
"""
Temp & Relay Dashboard v2.6
──────────────────────────────────────────────────────────────
• GUI: 2 temps, 6 cell voltages, SOC, SOH, charge-trend light,
        4 relay buttons, user-settable battery target °C
• Auto-Pilot logic:
        – heater / solenoid / pump follow user set-point reliably
• Excel logging on Auto-Pilot start/stop
• Live temp graph window (battery + heater)
• Live 6-cell battery window
• NEW: Displays Pack Voltage under graph
──────────────────────────────────────────────────────────────
pip install pyserial matplotlib openpyxl
"""

import os, sys, time, datetime, threading, queue, serial, tkinter as tk
from tkinter import ttk, messagebox
from collections import deque
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from openpyxl import Workbook
from temp_graph_windows import DualTempGraph
from cell_monitor_window import run_monitor, push_cell_data

PORT       = "/dev/cu.usbmodem212201"
BAUD       = 115200
REFRESH_MS = 40
PACK_MAX   = 25.2
CELL_FULL  = 4.20
LOG_DIR    = "/Users/princed/Desktop/DATA/"

RELAYS = [("Heater", 1),
          ("Solenoid", 2),
          ("Pump", 3),
          ("LOAD", 4)]

TREND_WINDOW = 30
TREND_THRESH = 0.01

def serial_reader(ser: serial.Serial, q: queue.Queue, stop_evt: threading.Event):
    ser.reset_input_buffer()
    while not stop_evt.is_set():
        try:
            line = ser.readline().decode(errors="ignore").strip()
        except serial.SerialException as err:
            q.put(("__ERR__", str(err))); break
        if line.startswith("DATA"):
            try:
                _, *nums = line.split(',')
                if len(nums) == 8:
                    q.put(tuple(map(float, nums)))
            except ValueError:
                pass

class Dashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Battery Dashboard + Auto-Pilot")
        self.resizable(False, False)
        BIG = ("Helvetica", 15, "bold")

        self.tvars = [tk.StringVar(value="--.-"), tk.StringVar(value="--.-")]
        tf = ttk.LabelFrame(self, text="Temperature (°C)")
        tf.grid(row=0, column=0, padx=6, pady=4, sticky="nsew")
        for i, lbl in enumerate(("Heater", "Battery")):
            ttk.Label(tf, text=f"{lbl}:").grid(row=i, column=0, sticky="w")
            ttk.Label(tf, textvariable=self.tvars[i], font=BIG).grid(row=i, column=1, sticky="e")

        self.vvars = [tk.StringVar(value="-.--") for _ in range(6)]
        self.soc_var, self.soh_var = tk.StringVar(), tk.StringVar()
        vf = ttk.LabelFrame(self, text="Cells & State")
        vf.grid(row=1, column=0, padx=6, pady=4, sticky="nsew")
        for i in range(6):
            ttk.Label(vf, text=f"Cell {i+1}:").grid(row=i, column=0, sticky="w")
            ttk.Label(vf, textvariable=self.vvars[i], font=BIG).grid(row=i, column=1, sticky="e")
        ttk.Separator(vf).grid(row=6, columnspan=2, sticky="ew", pady=2)
        ttk.Label(vf, text="SOC:").grid(row=7, column=0, sticky="w")
        ttk.Label(vf, textvariable=self.soc_var, font=BIG).grid(row=7, column=1, sticky="e")
        ttk.Label(vf, text="SOH:").grid(row=8, column=0, sticky="w")
        ttk.Label(vf, textvariable=self.soh_var, font=BIG).grid(row=8, column=1, sticky="e")

        self.trend_lbl = tk.Label(self, width=14, height=2, text="Trend",
                                  bg="grey80", font=("Helvetica", 11))
        self.trend_lbl.grid(row=2, column=0, pady=4)
        self.pack_window = deque(maxlen=TREND_WINDOW)

        self.state = {pin: False for _, pin in RELAYS}
        self.btn = {}
        rf = ttk.LabelFrame(self, text="Relays (active-LOW)")
        rf.grid(row=0, column=1, rowspan=3, padx=6, pady=4)
        for r, (name, pin) in enumerate(RELAYS):
            b = tk.Button(rf, width=10, height=2, text=f"{name}\nOFF",
                          bg="light grey",
                          command=lambda p=pin: self.toggle(p))
            b.grid(row=r, column=0, padx=4, pady=4)
            self.btn[pin] = b

        self.setpoint_var = tk.DoubleVar(value=20.0)
        spf = ttk.LabelFrame(self, text="Target Battery Temp (°C)")
        spf.grid(row=2, column=1, padx=6, pady=4, sticky="n")
        sp_entry = ttk.Entry(spf, width=6, textvariable=self.setpoint_var, font=("Consolas", 12))
        sp_entry.pack(padx=4, pady=2)
        sp_entry.bind("<Return>", lambda e: None)

        self.auto = False
        self.auto_btn = tk.Button(self, width=20, font=BIG,
                                  text="Enable Auto-Pilot", bg="light blue",
                                  command=self.toggle_auto)
        self.auto_btn.grid(row=3, column=0, columnspan=2, pady=6)

        self.fig = Figure(figsize=(4,3), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set(title="Pack Voltage", xlabel="t (s)", ylabel="V"); self.ax.grid(True)
        self.line, = self.ax.plot([], [], lw=1.8)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().grid(row=0, column=2, rowspan=4, padx=6, pady=4)

        self.pack_voltage_var = tk.StringVar(value="--.- V")
        ttk.Label(self, textvariable=self.pack_voltage_var, font=("Helvetica", 14, "bold"))\
            .grid(row=4, column=2, pady=5)

        try:
            self.ser = serial.Serial(PORT, BAUD, timeout=0.1)
            self.q, self.stop_evt = queue.Queue(), threading.Event()
            threading.Thread(target=serial_reader, args=(self.ser, self.q, self.stop_evt), daemon=True).start()
        except serial.SerialException as e:
            messagebox.showwarning("Serial", f"Serial port error:\n{e}\nGUI will still run.")
            self.ser = None
            self.q, self.stop_evt = queue.Queue(), threading.Event()

        self.t0 = time.time()
        self.time_buf, self.pack_buf = [], []
        self.cell_buf = [[] for _ in range(6)]
        self.wb = self.ws = None
        self.log_rows = []
        self.heat_start = None

        self.temp_window = DualTempGraph()
        self.after(1000, run_monitor)
        self.after(REFRESH_MS, self.update_gui)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def toggle(self, pin: int, force=None):
        self.state[pin] = force if force is not None else not self.state[pin]
        on = self.state[pin]
        name = next(n for n, p in RELAYS if p == pin)
        self.btn[pin].config(text=f"{name}\n{'ON' if on else 'OFF'}",
                             bg="spring green" if on else "light grey")
        if self.ser:
            try: self.ser.write(f"S,{pin},{int(on)}\n".encode())
            except serial.SerialException as e: messagebox.showerror("Serial", str(e))

    def toggle_auto(self):
        self.auto = not self.auto
        self.auto_btn.config(text="Disable Auto-Pilot" if self.auto else "Enable Auto-Pilot",
                             bg="pale green" if self.auto else "light blue")
        (self.start_session if self.auto else self.end_session)()

    def start_session(self):
        os.makedirs(LOG_DIR, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.xlsx_path = os.path.join(LOG_DIR, f"session_{ts}.xlsx")
        self.wb = Workbook(); self.ws = self.wb.active
        self.ws.append(["t_s", "tBatt", "tHeat", "Heater", "Solenoid", "Pump", "LOAD",
                        "PackV", "SOC%", "SOH%", "Charging", "HeatStart", "Heat∆s"])
        self.log_rows.clear(); self.heat_start = None

    def end_session(self):
        if not self.wb: return
        for r in self.log_rows: self.ws.append(r)
        try: self.wb.save(self.xlsx_path)
        except PermissionError:
            messagebox.showwarning("Save", "Close the Excel file then disable again.")
        self.wb = self.ws = None

    def update_gui(self):
        try:
            while True:
                item = self.q.get_nowait()
                if item and item[0] == "__ERR__":
                    messagebox.showerror("Serial", item[1]); self.on_close(); return

                t_batt, t_heat, *cumulative = item
                sorted_cum = sorted(cumulative)
                cells = [sorted_cum[0]] + [sorted_cum[i] - sorted_cum[i - 1] for i in range(1, 6)]

                self.tvars[0].set(f"{t_batt:4.1f}")
                self.tvars[1].set(f"{t_heat:4.1f}")
                for i, v in enumerate(cells): self.vvars[i].set(f"{v:.2f}")

                pack_v = max(cumulative)
                self.pack_voltage_var.set(f"{pack_v:.2f} V")

                soc = max(0, min(pack_v / PACK_MAX, 1)) * 100
                soh = max(0, min(sum(cells) / 6 / CELL_FULL, 1)) * 100
                self.soc_var.set(f"{soc:5.1f} %")
                self.soh_var.set(f"{soh:5.1f} %")

                self.pack_window.append(pack_v)
                if len(self.pack_window) == TREND_WINDOW:
                    delta = self.pack_window[-1] - self.pack_window[0]
                    if delta > TREND_THRESH: trend = "up"
                    elif delta < -TREND_THRESH: trend = "down"
                    else: trend = "flat"
                    self.trend_lbl.config(
                        text={"up": "Charging ↑", "down": "Discharging ↓", "flat": "Stable"}[trend],
                        bg={"up": "pale green", "down": "light coral", "flat": "grey80"}[trend])

                now = time.time() - self.t0
                self.time_buf.append(now); self.pack_buf.append(pack_v)
                for i in range(6): self.cell_buf[i].append(cells[i])
                if len(self.time_buf) > 300:
                    self.time_buf, self.pack_buf = self.time_buf[-300:], self.pack_buf[-300:]
                    for i in range(6): self.cell_buf[i] = self.cell_buf[i][-300:]
                self.line.set_data(self.time_buf, self.pack_buf)
                self.ax.relim(); self.ax.autoscale_view(); self.canvas.draw_idle()

                self.temp_window.add_data(t_batt, t_heat)
                push_cell_data(cumulative)

                if self.auto:
                    try:
                        S = float(self.setpoint_var.get())
                    except (tk.TclError, ValueError):
                        S = 20.0
                    h_pin, s_pin, p_pin = 1, 2, 3
                    heater_on = (t_batt < S) and (t_heat <= S + 20)
                    heater_off = (t_batt >= S) or (t_heat >= S + 20)
                    pump_on = (t_batt < S) and (t_heat >= t_batt + 10)
                    pump_off = (t_batt >= S)

                    if heater_on: self.toggle(h_pin, True)
                    elif heater_off: self.toggle(h_pin, False)
                    if pump_on: self.toggle(s_pin, True); self.toggle(p_pin, True)
                    elif pump_off: self.toggle(s_pin, False); self.toggle(p_pin, False)

                    if self.state[h_pin] and self.heat_start is None:
                        self.heat_start = now
                    heat_delta = (now - self.heat_start) if (self.heat_start and not self.state[h_pin]) else ""

                    self.log_rows.append([now, t_batt, t_heat,
                                          int(self.state[1]), int(self.state[2]), int(self.state[3]), int(self.state[4]),
                                          pack_v, soc, soh,
                                          trend == "up",
                                          self.heat_start if self.heat_start else "",
                                          heat_delta])
        except queue.Empty:
            pass
        self.after(REFRESH_MS, self.update_gui)

    def on_close(self):
        if self.auto: self.end_session()
        self.stop_evt.set()
        try:
            self.ser and self.ser.close()
        except Exception: pass
        self.destroy()

if __name__ == "__main__":
    try:
        import serial, matplotlib, openpyxl
    except ModuleNotFoundError as err:
        sys.exit("Install:\n  pip install pyserial matplotlib openpyxl\n" + str(err))
    Dashboard().mainloop()

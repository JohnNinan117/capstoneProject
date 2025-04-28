import tkinter as tk, time
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class DualTempGraph(tk.Toplevel):
    """
    • Shows Battery & Heater temps in one window
    • 30 s sliding window, updates via .add_data(batt, heat)
    """
    def __init__(self):
        super().__init__()
        self.title("Live Temperatures (30 s window)")
        self.geometry("550x420")

        self.start_t = time.time()
        self.t_data  = []          # shared time axis
        self.batt    = []
        self.heat    = []
        self.b_min = self.h_min = float('inf')
        self.b_max = self.h_max = float('-inf')

        fig = Figure(figsize=(5.3, 3.5), dpi=100)
        self.ax = fig.add_subplot(111)
        self.b_line, = self.ax.plot([], [], color="blue",  label="Battery °C")
        self.h_line, = self.ax.plot([], [], color="red",   label="Heater °C")
        self.ax.set_xlabel("Time (s)"); self.ax.set_ylabel("Temp (°C)")
        self.ax.grid(True); self.ax.legend()
        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.min_lbl = ttk.Label(self, text="Min batt: --   Min heat: --")
        self.max_lbl = ttk.Label(self, text="Max batt: --   Max heat: --")
        self.min_lbl.pack(side=tk.LEFT,  padx=10)
        self.max_lbl.pack(side=tk.RIGHT, padx=10)

        self.after(500, self._refresh)

    def add_data(self, batt_val, heat_val):
        t = time.time() - self.start_t
        self.t_data.append(t)
        self.batt.append(batt_val)
        self.heat.append(heat_val)
        self.b_min, self.b_max = min(self.b_min, batt_val), max(self.b_max, batt_val)
        self.h_min, self.h_max = min(self.h_min, heat_val), max(self.h_max, heat_val)

        # trim >30 s
        while self.t_data and (t - self.t_data[0] > 30):
            self.t_data.pop(0); self.batt.pop(0); self.heat.pop(0)

    def _refresh(self):
        if self.t_data:
            self.b_line.set_data(self.t_data, self.batt)
            self.h_line.set_data(self.t_data, self.heat)
            self.ax.relim(); self.ax.autoscale_view()
            self.canvas.draw()
            self.min_lbl.config(
                text=f"Min batt: {self.b_min:.1f}°C   "
                     f"Min heat: {self.h_min:.1f}°C")
            self.max_lbl.config(
                text=f"Max batt: {self.b_max:.1f}°C   "
                     f"Max heat: {self.h_max:.1f}°C")
        self.after(500, self._refresh)

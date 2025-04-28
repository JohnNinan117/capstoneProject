

import tkinter as tk, queue, time

MAX_V = 4.20
NUM   = 6

_q = queue.Queue(maxsize=1)

def push_cell_data(cumulative):
    try:
        while True: _q.get_nowait()
    except queue.Empty:
        pass
    _q.put(cumulative)

def soc_color(pct: float) -> str:
    if pct >= 80: return "#00d000"
    if pct >= 60: return "#70d000"
    if pct >= 40: return "#c0c000"
    if pct >= 20: return "#d07000"
    return "#d00000"

class BatteryIcon:
    def __init__(self, canvas: tk.Canvas, x: int, y: int, w: int = 40, h: int = 100):
        self.cv, self.x, self.y, self.w, self.h = canvas, x, y, w, h
        self.cv.create_rectangle(x, y, x+w, y+h, width=2, outline="#aaa")
        self.cv.create_rectangle(x + w*0.3, y-8, x + w*0.7, y, fill="#555", outline="")
        self.fill = self.cv.create_rectangle(x+3, y+h-3, x+w-3, y+h-3, width=0, fill="#00d000")

    def update(self, pct: float):
        pct = max(0, min(pct, 100))
        h_fill = (self.h-6) * pct/100
        self.cv.coords(self.fill, self.x+3, self.y + self.h-3 - h_fill,
                       self.x+self.w-3, self.y+self.h-3)
        self.cv.itemconfig(self.fill, fill=soc_color(pct))

class CellMonitor(tk.Toplevel):
    def __init__(self):
        super().__init__()
        self.title("6-Cell Battery Monitor")
        self.geometry("700x720")
        self.configure(bg="#1e1e1e")

        wrapper = tk.Frame(self, bg="#1e1e1e")
        wrapper.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(wrapper, width=100, height=NUM*110, bg="#1e1e1e", highlightthickness=0)
        self.canvas.grid(row=0, column=0, rowspan=NUM+1, sticky="nsw", padx=(0, 20))

        info_hdr = ["Cell", "V", "%", "Min", "Max"]
        for c, text in enumerate(info_hdr):
            lbl = tk.Label(wrapper, text=text, fg="white", bg="#1e1e1e",
                           font=("Consolas", 11, "bold"))
            lbl.grid(row=0, column=c+1, sticky="w", padx=6)

        self.icons = []
        self.stats = []
        self.mins = [10.0] * NUM
        self.maxs = [0.0] * NUM

        for i in range(NUM):
            y = i * 110 + 10
            self.icons.append(BatteryIcon(self.canvas, 10, y, 40, 100))

            lbl = tk.Label(wrapper, text=f"{i+1}", font=("Consolas", 11), fg="#4fc3f7", bg="#1e1e1e")
            val = tk.Label(wrapper, font=("Consolas", 11), fg="white", bg="#1e1e1e")
            pct = tk.Label(wrapper, font=("Consolas", 11), fg="white", bg="#1e1e1e")
            mn  = tk.Label(wrapper, font=("Consolas", 11), fg="white", bg="#1e1e1e")
            mx  = tk.Label(wrapper, font=("Consolas", 11), fg="white", bg="#1e1e1e")
            for j, w in enumerate((lbl, val, pct, mn, mx), start=1):
                w.grid(row=i+1, column=j, sticky="w", padx=6, pady=4)
            self.stats.append((val, pct, mn, mx))

        self.after(50, self._pump)

    def _pump(self):
        try:
            cumulative = _q.get_nowait()
            if len(cumulative) != 6:
                return
            sorted_cum = sorted(cumulative)
            cells = [sorted_cum[0]] + [sorted_cum[i] - sorted_cum[i-1] for i in range(1, 6)]

            for idx, v in enumerate(cells):
                pct = (v / MAX_V) * 100
                self.icons[idx].update(pct)

                self.mins[idx] = min(self.mins[idx], v)
                self.maxs[idx] = max(self.maxs[idx], v)

                val, pct_l, mn, mx = self.stats[idx]
                val.config(text=f"{v:.2f}")
                pct_l.config(text=f"{pct:.1f}")
                mn.config(text=f"{self.mins[idx]:.2f}")
                mx.config(text=f"{self.maxs[idx]:.2f}")
        except queue.Empty:
            pass
        self.after(50, self._pump)

def run_monitor():
    CellMonitor()

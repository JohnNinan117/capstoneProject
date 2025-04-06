import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os, json, hashlib, binascii
import random
import time
import logging

# Set up logging to file
logging.basicConfig(
    filename='alarm.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- Helper Function for SoC Calculation ---
def voltage_to_soc(voltage):
    """
    Calculate SoC based on a linear mapping:
    3.00V  -> 0% SoC
    4.00V  -> 100% SoC
    """
    soc = (voltage - 3.00) / (4.00 - 3.00) * 100
    return max(0, min(soc, 100))

# --- Dummy Serial Class for Simulation ---
class DummySerial:
    def __init__(self, baudrate=9600, timeout=1):
        self.baudrate = baudrate
        self.timeout = timeout
        self.in_waiting = True  # Always simulate that data is available

    def readline(self):
        # Simulate sensor values for 12 channels (for 12 batteries) between 3.00V and 4.00V.
        values = [f"{random.uniform(3.00, 4.00):.2f}" for _ in range(12)]
        time.sleep(0.1)  # Simulate a small delay
        return (",".join(values) + "\n").encode('utf-8')

# --- Password Hashing Utilities ---
def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return binascii.hexlify(salt).decode('ascii'), binascii.hexlify(hashed).decode('ascii')

def verify_password(stored_salt, stored_hash, provided_password):
    salt = binascii.unhexlify(stored_salt.encode('ascii'))
    hashed = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
    return stored_hash == binascii.hexlify(hashed).decode('ascii')

# --- RegistrationFrame ---
class RegistrationFrame(tk.Frame):
    def __init__(self, master, switch_to_login):
        super().__init__(master, bg="#063028")
        self.switch_to_login = switch_to_login
        self.create_widgets()
    
    def create_widgets(self):
        tk.Label(self, text="Register", font=("Helvetica", 20, "bold"),
                 bg="#063028", fg="white").pack(pady=10)
        tk.Label(self, text="Username", bg="#063028", fg="white").pack()
        self.username_entry = tk.Entry(self)
        self.username_entry.pack()
        tk.Label(self, text="Password", bg="#063028", fg="white").pack()
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack()
        tk.Button(self, text="Register", command=self.register_user).pack(pady=10)
        tk.Button(self, text="Already have an account? Login", command=self.switch_to_login).pack(pady=5)
    
    def register_user(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        users = {}
        if os.path.exists("users.json"):
            with open("users.json", "r") as f:
                users = json.load(f)
        if username in users:
            messagebox.showerror("Error", "Username already exists")
            return
        salt, hashed = hash_password(password)
        users[username] = {"salt": salt, "hash": hashed}
        with open("users.json", "w") as f:
            json.dump(users, f)
        messagebox.showinfo("Success", "Registration successful!")
        self.switch_to_login()

# --- LoginFrame ---
class LoginFrame(tk.Frame):
    def __init__(self, master, login_success, switch_to_register):
        super().__init__(master, bg="#063028")
        self.login_success = login_success
        self.switch_to_register = switch_to_register
        self.create_widgets()
    
    def create_widgets(self):
        tk.Label(self, text="Login", font=("Helvetica", 20, "bold"),
                 bg="#063028", fg="white").pack(pady=10)
        tk.Label(self, text="Username", bg="#063028", fg="white").pack()
        self.username_entry = tk.Entry(self)
        self.username_entry.pack()
        tk.Label(self, text="Password", bg="#063028", fg="white").pack()
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack()
        tk.Button(self, text="Login", command=self.login).pack(pady=10)
        tk.Button(self, text="Don't have an account? Register", command=self.switch_to_register).pack(pady=5)
    
    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        if not os.path.exists("users.json"):
            messagebox.showerror("Error", "No registered users. Please register first.")
            return
        with open("users.json", "r") as f:
            users = json.load(f)
        if username in users:
            stored = users[username]
            if verify_password(stored["salt"], stored["hash"], password):
                messagebox.showinfo("Success", "Login successful!")
                self.login_success(username)
                return
        messagebox.showerror("Error", "Invalid username or password")

# --- NavigationView ---
class NavigationView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#063028")
        self.battery6_image = None
        self.load_battery6_image()
        self.create_widgets()
    
    def load_battery6_image(self):
        path = os.path.join(os.path.dirname(__file__), "iconsAndImages", "battery(6).png")
        if not os.path.exists(path):
            messagebox.showerror("Error", f"Battery(6) image not found: {path}")
            return
        img = Image.open(path)
        w, h = img.size
        new_w = int(w * 0.5)
        new_h = int(h * 0.5)
        resized_img = img.resize((new_w, new_h))
        self.battery6_image = ImageTk.PhotoImage(resized_img)
    
    def create_widgets(self):
        canvas = tk.Canvas(self, width=self.battery6_image.width(), height=self.battery6_image.height(),
                           bg="#063028", highlightthickness=0)
        canvas.pack(pady=10)
        canvas.create_image(0, 0, image=self.battery6_image, anchor='nw')
        
        title = tk.Label(self, text="Main Menu", font=("Helvetica", 24, "bold"),
                         bg="#063028", fg="white")
        title.pack(pady=20)
        
        system_lbl = tk.Label(self, text="System View", font=("Helvetica", 16, "bold"),
                              bg="#063028", fg="white")
        system_lbl.pack(pady=10)
        system_lbl.bind("<Button-1>", lambda e: self.master.show_view(self.master.system_view))
        
        alarm_lbl = tk.Label(self, text="Alarm View", font=("Helvetica", 16, "bold"),
                             bg="#063028", fg="white")
        alarm_lbl.pack(pady=10)
        alarm_lbl.bind("<Button-1>", lambda e: self.master.show_view(self.master.alarm_view))
        
        about_lbl = tk.Label(self, text="About", font=("Helvetica", 16, "bold"),
                             bg="#063028", fg="white")
        about_lbl.pack(pady=10)
        about_lbl.bind("<Button-1>", lambda e: self.master.show_view(self.master.about_view))

# --- SystemView ---
class SystemView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#063028")
        self.rect9_image = None
        self.rect26_image = None  # Normal overall panel image.
        self.rect27_image = None  # Active overall panel image (unused here).
        self.battery10_image = None  # Image for active alarm state for battery icons.
        self.image5 = None
        self.arrow_image = None
        self.serial_obj = None   # Dummy serial connection.
        # Lists for battery icon text references.
        self.center_text_items = []
        self.secondary_text_items = []
        self.temperature_text_items = []
        self.center_text_canvases = []
        # List to store shutdown message IDs for battery icons.
        self.shutdown_text_items = []
        # Dictionary for overall panel text items.
        self.rect_text_items = {}
        self.alarm_manual_active = False  # Manual alarm override flag.
        self.load_all_images()

        # Create overall system panels.
        rect_positions = [(120, 80), (330, 80), (540, 80), (750, 80), (960, 80)]
        rect_labels = ["SoC:", "SoH:", "Voltage:", "Temp:", "Alarm Status:"]
        initial_values = ["0%", "0%", "0.00V", "0°C", "Clear"]
        for idx, (x, y) in enumerate(rect_positions):
            canvas = tk.Canvas(self, width=self.rect9_image.width(), height=self.rect9_image.height(),
                               bg="#063028", highlightthickness=0)
            canvas.place(x=x, y=y)
            # For the last panel, use Rectangle 26 image (normal state).
            if idx == len(rect_positions) - 1:
                canvas.create_image(0, 0, image=self.rect26_image, anchor='nw')
            else:
                canvas.create_image(0, 0, image=self.rect9_image, anchor='nw')
            canvas.create_text(self.rect9_image.width()/2, 5, text=rect_labels[idx],
                               fill="white", font=("Helvetica", 14, "bold"), anchor='n')
            text_id = canvas.create_text(self.rect9_image.width()/2, self.rect9_image.height()/2,
                                          text=initial_values[idx], fill="white", font=("Helvetica", 20, "bold"), anchor='center')
            self.rect_text_items[rect_labels[idx]] = (canvas, text_id)
        
        # Bind click event on overall Alarm Status panel.
        alarm_canvas, _ = self.rect_text_items["Alarm Status:"]
        alarm_canvas.bind("<Button-1>", self.toggle_alarm_status)
        
        # Create battery icon canvases for individual cells.
        start_x = 70
        gap = 200
        # First row: Cells C1 to C6.
        for i in range(6):
            x_pos = start_x + i * gap
            canvas = tk.Canvas(self, width=self.image5.width(), height=self.image5.height(),
                               bg="#063028", highlightthickness=0)
            canvas.place(x=x_pos, y=300)
            # Create the background with tag "bg".
            canvas.create_image(0, 0, image=self.image5, anchor='nw', tags="bg")
            battery_label = "C" + str(i + 1)
            canvas.create_text(self.image5.width()//2, 35, text=battery_label,
                               fill="#DEEBDD", font=("Helvetica", 24, "bold"), anchor="n")
            center_text_id = canvas.create_text(self.image5.width()//2, self.image5.height()//2,
                                                 text="0", fill="white", font=("Helvetica", 14, "bold"), anchor="center")
            self.center_text_items.append(center_text_id)
            secondary_text_id = canvas.create_text(self.image5.width()//2, self.image5.height()//2 + 20,
                                                    text="Voltage:", fill="white", font=("Helvetica", 12, "bold"), anchor="center")
            self.secondary_text_items.append(secondary_text_id)
            temperature_text_id = canvas.create_text(self.image5.width()//2, self.image5.height()//2 + 40,
                                                      text="T: 0°C", fill="white", font=("Helvetica", 12, "bold"), anchor="center")
            self.temperature_text_items.append(temperature_text_id)
            self.center_text_canvases.append(canvas)
            self.shutdown_text_items.append(None)
        
        # Second row: Cells C7 to C12.
        for i in range(6):
            x_pos = start_x + i * gap
            canvas = tk.Canvas(self, width=self.image5.width(), height=self.image5.height(),
                               bg="#063028", highlightthickness=0)
            canvas.place(x=x_pos, y=440)
            canvas.create_image(0, 0, image=self.image5, anchor='nw', tags="bg")
            battery_label = "C" + str(i + 7)
            canvas.create_text(self.image5.width()//2, 35, text=battery_label,
                               fill="#DEEBDD", font=("Helvetica", 24, "bold"), anchor="n")
            center_text_id = canvas.create_text(self.image5.width()//2, self.image5.height()//2,
                                                 text="0", fill="white", font=("Helvetica", 14, "bold"), anchor="center")
            self.center_text_items.append(center_text_id)
            secondary_text_id = canvas.create_text(self.image5.width()//2, self.image5.height()//2 + 20,
                                                    text="Voltage:", fill="white", font=("Helvetica", 12, "bold"), anchor="center")
            self.secondary_text_items.append(secondary_text_id)
            temperature_text_id = canvas.create_text(self.image5.width()//2, self.image5.height()//2 + 40,
                                                      text="T: 0°C", fill="white", font=("Helvetica", 12, "bold"), anchor="center")
            self.temperature_text_items.append(temperature_text_id)
            self.center_text_canvases.append(canvas)
            self.shutdown_text_items.append(None)
        
        # Add back arrow at top left.
        lbl_arrow = tk.Label(self, image=self.master.arrow_image, bg="#063028")
        lbl_arrow.place(x=20, y=20)
        lbl_arrow.bind("<Button-1>", lambda event: self.go_back())
        
        self.after(1000, self.update_sensor_values)
    
    def load_all_images(self):
        # Load Rectangle 9.png and resize to 45% of original dimensions.
        rect_img_path = os.path.join(os.path.dirname(__file__), "iconsAndImages", "Rectangle 9.png")
        if not os.path.exists(rect_img_path):
            messagebox.showerror("Error", f"Rectangle 9 image not found: {rect_img_path}")
            return
        rect_img = Image.open(rect_img_path)
        w, h = rect_img.size
        new_w = int(w * 0.45)
        new_h = int(h * 0.45)
        resized_rect = rect_img.resize((new_w, new_h))
        self.rect9_image = ImageTk.PhotoImage(resized_rect)
        
        # Load Rectangle 26.png for normal overall alarm panel.
        rect26_path = os.path.join(os.path.dirname(__file__), "iconsAndImages", "Rectangle 26.png")
        if not os.path.exists(rect26_path):
            messagebox.showerror("Error", f"Rectangle 26 image not found: {rect26_path}")
            return
        rect26_img = Image.open(rect26_path)
        resized_rect26 = rect26_img.resize((new_w, new_h))
        self.rect26_image = ImageTk.PhotoImage(resized_rect26)
        
        # Load Rectangle 27.png for active overall alarm panel (unused here).
        rect27_path = os.path.join(os.path.dirname(__file__), "iconsAndImages", "Rectangle 27.png")
        if not os.path.exists(rect27_path):
            messagebox.showerror("Error", f"Rectangle 27 image not found: {rect27_path}")
            return
        rect27_img = Image.open(rect27_path)
        resized_rect27 = rect27_img.resize((new_w, new_h))
        self.rect27_image = ImageTk.PhotoImage(resized_rect27)
        
        # Load battery (10).png for active alarm state for battery icons.
        battery10_path = os.path.join(os.path.dirname(__file__), "iconsAndImages", "battery (10).png")
        if not os.path.exists(battery10_path):
            messagebox.showerror("Error", f"Battery (10) image not found: {battery10_path}")
            return
        battery10_img = Image.open(battery10_path)
        # Adjust the size as desired; here we use the same new_w, new_h as the overall panels.
        resized_battery10 = battery10_img.resize((int(new_w * 0.9), int(new_h * 0.9)))
        self.battery10_image = ImageTk.PhotoImage(resized_battery10)
        
        # Load Image 5.png and resize to 35% of original dimensions.
        image5_path = os.path.join(os.path.dirname(__file__), "iconsAndImages", "Image 5.png")
        if not os.path.exists(image5_path):
            messagebox.showerror("Error", f"Image 5 not found: {image5_path}")
            return
        img5 = Image.open(image5_path)
        w5, h5 = img5.size
        new_w5 = int(w5 * 0.35)
        new_h5 = int(h5 * 0.35)
        resized_img5 = img5.resize((new_w5, new_h5))
        self.image5 = ImageTk.PhotoImage(resized_img5)
        
        # Load Arrow 1.png without resizing.
        arrow_img_path = os.path.join(os.path.dirname(__file__), "iconsAndImages", "Arrow 1.png")
        if not os.path.exists(arrow_img_path):
            messagebox.showerror("Error", f"Arrow 1 image not found: {arrow_img_path}")
            return
        arrow_img = Image.open(arrow_img_path)
        self.arrow_image = ImageTk.PhotoImage(arrow_img)
        
        # Create dummy serial connection.
        try:
            self.serial_obj = DummySerial(baudrate=9600, timeout=1)
        except Exception as e:
            messagebox.showerror("Error", f"Error creating dummy serial: {e}")
            self.serial_obj = None
    
    def toggle_alarm_status(self, event):
        self.alarm_manual_active = not self.alarm_manual_active
        print("Manual alarm override set to", self.alarm_manual_active)
    
    def update_sensor_values(self):
        if self.serial_obj:
            try:
                line = self.serial_obj.readline().decode('utf-8').strip()
                if line:
                    values = line.split(',')
                    if len(values) >= 12:
                        battery_temps = []
                        # Update each battery icon.
                        for i, canvas in enumerate(self.center_text_canvases):
                            voltage = float(values[i])
                            cell_soc = voltage_to_soc(voltage)
                            temp_val = random.uniform(25, 40)
                            battery_temps.append(temp_val)
                        overall_temp = sum(battery_temps) / len(battery_temps)
                        
                        if self.alarm_manual_active or overall_temp > 40:
                            # Alarm active: update battery icon backgrounds to battery (10).png and display shutdown message.
                            for i, canvas in enumerate(self.center_text_canvases):
                                canvas.delete("bg")
                                canvas.create_image(0, 0, image=self.battery10_image, anchor='nw', tags="bg")
                                canvas.tag_lower("bg")
                                canvas.itemconfig(self.center_text_items[i],
                                                text="Safety Shutdown Active",
                                                fill="#DEEBDD",
                                                font=("Helvetica", int(9), "bold"))
                                    
                                canvas.itemconfig(self.secondary_text_items[i], text="", fill="white")
                                canvas.itemconfig(self.temperature_text_items[i], text="", fill="white")
                        else:
                            # Normal state: update each battery icon normally.
                            for i, canvas in enumerate(self.center_text_canvases):
                                voltage = float(values[i])
                                cell_soc = voltage_to_soc(voltage)
                                temp_val = battery_temps[i]
                                canvas.delete("bg")
                                canvas.create_image(0, 0, image=self.image5, anchor='nw', tags="bg")
                                canvas.tag_lower("bg")
                                canvas.itemconfig(self.center_text_items[i], text="Voltage: " + values[i], fill="#DEEBDD")
                                canvas.itemconfig(self.secondary_text_items[i], text="SoC: " + f"{cell_soc:.0f}%", fill="#DEEBDD")
                                canvas.itemconfig(self.temperature_text_items[i], text="Temp: " + f"{temp_val:.0f}°C", fill="#DEEBDD")
                                if self.shutdown_text_items[i] is not None:
                                    canvas.delete(self.shutdown_text_items[i])
                                    self.shutdown_text_items[i] = None
                        
                        # Compute overall system values.
                        battery_values = [float(v) for v in values]
                        average_voltage = sum(battery_values) / len(battery_values)
                        overall_soc = voltage_to_soc(average_voltage)
                        overall_soh = random.uniform(90, 100)
                        overall_temp = sum(battery_temps) / len(battery_temps)
                        
                        # Update overall panels.
                        canvas, text_id = self.rect_text_items["SoC:"]
                        canvas.itemconfig(text_id, text=f"{overall_soc:.0f}%")
                        canvas, text_id = self.rect_text_items["SoH:"]
                        canvas.itemconfig(text_id, text=f"{overall_soh:.0f}%")
                        canvas, text_id = self.rect_text_items["Voltage:"]
                        canvas.itemconfig(text_id, text=f"{average_voltage:.2f}V")
                        canvas, text_id = self.rect_text_items["Temp:"]
                        canvas.itemconfig(text_id, text=f"{overall_temp:.0f}°C")
                        
                        # Update overall Alarm Status panel.
                        alarm_canvas, _ = self.rect_text_items["Alarm Status:"]
                        alarm_canvas.delete("all")
                        if self.alarm_manual_active or overall_temp > 40:
                            logging.info("Alarm Active: Temperature exceeded threshold or manual override triggered.")
                            alarm_canvas.create_image(0, 0, image=self.rect27_image, anchor='nw')
                            alarm_canvas.create_text(self.rect27_image.width()/2, 5, text="Alarm Status:",
                                                       fill="white", font=("Helvetica", 14, "bold"), anchor="n")
                            alarm_canvas.create_text(self.rect27_image.width()/2, self.rect27_image.height()/2,
                                                       text="Active", fill="white", font=("Helvetica", 20, "bold"), anchor="center")
                        else:
                            logging.info("Alarm Clear: Temperature within normal range.")
                            alarm_canvas.create_image(0, 0, image=self.rect26_image, anchor='nw')
                            alarm_canvas.create_text(self.rect26_image.width()/2, 5, text="Alarm Status:",
                                                       fill="white", font=("Helvetica", 14, "bold"), anchor="n")
                            alarm_canvas.create_text(self.rect26_image.width()/2, self.rect26_image.height()/2,
                                                       text="Clear", fill="white", font=("Helvetica", 20, "bold"), anchor="center")
            except Exception as e:
                print("Error reading sensor values:", e)
        self.after(1000, self.update_sensor_values)
    
    def go_back(self):
        self.pack_forget()
        self.master.show_view(self.master.navigation_view)

# --- AlarmView ---
class AlarmView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#063028")
        label = tk.Label(self, text="Alarm View", font=("Helvetica", 24, "bold"), bg="#063028", fg="white")
        label.pack(pady=20)
        lbl_arrow = tk.Label(self, image=self.master.arrow_image, bg="#063028")
        lbl_arrow.place(x=20, y=20)
        lbl_arrow.bind("<Button-1>", lambda e: self.master.show_view(self.master.navigation_view))
        back = tk.Label(self, text="Back", font=("Helvetica", 16, "bold"), bg="#063028", fg="white")
        back.pack(pady=10)
        back.bind("<Button-1>", lambda e: self.master.show_view(self.master.navigation_view))

# --- AboutView ---
class AboutView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#063028")
        label = tk.Label(self, text="About", font=("Helvetica", 24, "bold"), bg="#063028", fg="white")
        label.pack(pady=20)
        lbl_arrow = tk.Label(self, image=self.master.arrow_image, bg="#063028")
        lbl_arrow.place(x=20, y=20)
        lbl_arrow.bind("<Button-1>", lambda e: self.master.show_view(self.master.navigation_view))
        back = tk.Label(self, text="Back", font=("Helvetica", 16, "bold"), bg="#063028", fg="white")
        back.pack(pady=10)
        back.bind("<Button-1>", lambda e: self.master.show_view(self.master.navigation_view))

# --- BMSApp ---
class BMSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Battery Management System")
        self.geometry("1280x720")
        self.configure(bg="#063028")
        self.arrow_image = self.load_arrow_image()
        self.navigation_view = NavigationView(self)
        self.system_view = SystemView(self)
        self.alarm_view = AlarmView(self)
        self.about_view = AboutView(self)
        self.login_frame = None
        self.registration_frame = None
        self.current_view = None
        self.show_login()
    
    def load_arrow_image(self):
        arrow_img_path = os.path.join(os.path.dirname(__file__), "iconsAndImages", "Arrow 1.png")
        if not os.path.exists(arrow_img_path):
            messagebox.showerror("Error", f"Arrow 1 image not found: {arrow_img_path}")
            return None
        arrow_img = Image.open(arrow_img_path)
        return ImageTk.PhotoImage(arrow_img)
    
    def show_view(self, view_frame):
        if self.current_view is not None:
            self.current_view.place_forget()
        view_frame.place(x=0, y=0, relwidth=1, relheight=1)
        self.current_view = view_frame
    
    def show_login(self):
        if self.current_view is not None:
            self.current_view.place_forget()
        if self.login_frame is not None:
            self.login_frame.destroy()
        self.login_frame = LoginFrame(self, self.on_login_success, self.show_registration)
        self.login_frame.place(x=0, y=0, relwidth=1, relheight=1)
        self.current_view = self.login_frame
    
    def show_registration(self):
        if self.current_view is not None:
            self.current_view.place_forget()
        if self.registration_frame is not None:
            self.registration_frame.destroy()
        self.registration_frame = RegistrationFrame(self, self.show_login)
        self.registration_frame.place(x=0, y=0, relwidth=1, relheight=1)
        self.current_view = self.registration_frame
    
    def on_login_success(self, username):
        messagebox.showinfo("Welcome", f"Welcome, {username}!")
        self.show_view(self.navigation_view)

if __name__ == "__main__":
    app = BMSApp()
    app.mainloop()

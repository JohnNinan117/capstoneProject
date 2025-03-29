import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os, json, hashlib, binascii

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

# --- Authentication Frames ---
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

# --- Main Application Frames ---
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

class SystemView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#063028")
        self.rect9_image = None
        self.image5 = None
        self.arrow_image = None
        self.load_all_images()

        # Define positions and text values for the rectangle canvases.
        rect_positions = [(120, 80), (330, 80), (540, 80), (750, 80), (960, 80)]
        rect_labels = ["SoC:", "SoH:", "Voltage:", "Current:", "Temp:"]
        rect_data = ["80%", "58%", "12.5V", "5A", "35°C"]
        
        for idx, (x, y) in enumerate(rect_positions):
            canvas = tk.Canvas(self, width=self.rect9_image.width(), height=self.rect9_image.height(),
                               bg="#063028", highlightthickness=0)
            canvas.place(x=x, y=y)
            canvas.create_image(0, 0, image=self.rect9_image, anchor='nw')
            canvas.create_text(self.rect9_image.width()/2, 5, text=rect_labels[idx],
                               fill="white", font=("Helvetica", 14, "bold"), anchor='n')
            canvas.create_text(self.rect9_image.width()/2, self.rect9_image.height()/2,
                               text=rect_data[idx], fill="white", font=("Helvetica", 20, "bold"), anchor='center')
        
        # Place 6 instances of "Image 5" (first row) with two texts on each image.
        # Top text will now be labeled "c1", "c2", ..., and moved from y=5 to y=35.
        start_x = 70
        gap = 200
        for i in range(6):
            x_pos = start_x + i * gap
            canvas = tk.Canvas(self, width=self.image5.width(), height=self.image5.height(),
                               bg="#063028", highlightthickness=0)
            canvas.place(x=x_pos, y=300)
            canvas.create_image(0, 0, image=self.image5, anchor='nw')
            battery_label = "C" + str(i + 1)  # For first row: c1, c2, ..., c6
            canvas.create_text(self.image5.width()//2, 35, text=battery_label,
                               fill="white", font=("Helvetica", 14, "bold"), anchor="n")
            canvas.create_text(self.image5.width()//2, self.image5.height()//2, text="Center Text",
                               fill="white", font=("Helvetica", 14, "bold"), anchor="center")
        
        # Place 6 instances of "Image 5" (second row) with two texts on each image.
        # Top text labels will be c7, c8, ..., c12.
        for i in range(6):
            x_pos = start_x + i * gap
            canvas = tk.Canvas(self, width=self.image5.width(), height=self.image5.height(),
                               bg="#063028", highlightthickness=0)
            canvas.place(x=x_pos, y=440)
            canvas.create_image(0, 0, image=self.image5, anchor='nw')
            battery_label = "C" + str(i + 7)  # For second row: c7, c8, ..., c12
            canvas.create_text(self.image5.width()//2, 35, text=battery_label,
                               fill="white", font=("Helvetica", 14, "bold"), anchor="n")
            canvas.create_text(self.image5.width()//2, self.image5.height()//2, text="Center Text",
                               fill="white", font=("Helvetica", 14, "bold"), anchor="center")
        
        # Add the arrow (back button) at the top left corner.
        lbl_arrow = tk.Label(self, image=self.arrow_image, bg="#063028")
        lbl_arrow.place(x=20, y=20)
        lbl_arrow.bind("<Button-1>", lambda event: self.go_back())
    
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
    
    def go_back(self):
        self.pack_forget()
        self.master.show_view(self.master.navigation_view)

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

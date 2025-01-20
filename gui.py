import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os

def main():
    root = tk.Tk()
    root.title("Battery Management System")
    root.geometry("1280x720")
    root.configure(bg="#063028")

    # ----- TITLE LABEL -----
    title_label = tk.Label(
        root,
        text="Battery Management System",
        font=("Helvetica", 24, "bold"),
        bg="#063028",
        fg="white"
    )
    title_label.pack(side=tk.TOP, pady=20)

    # ----------------------------------------------------------------
    # 1) LOAD & DISPLAY THE BATTERY IMAGE
    # ----------------------------------------------------------------
    battery_image_path = os.path.join(
        os.path.dirname(__file__),
        "iconsAndImages",
        "battery (8).png"
    )

    if not os.path.exists(battery_image_path):
        messagebox.showerror("Error", f"Battery image not found: {battery_image_path}")
        root.destroy()
        return

    # Load, resize, and display the battery image
    battery_image = Image.open(battery_image_path)
    resized_battery_image = battery_image.resize((300, 300))  # Adjust size as needed
    battery_image_tk = ImageTk.PhotoImage(resized_battery_image)

    battery_label = tk.Label(
        root,
        image=battery_image_tk,
        bg="#063028"
    )
    battery_label.place(x=800, y=200)  # Position the battery image
    # Keep a reference
    battery_label.image = battery_image_tk

    # ----------------------------------------------------------------
    # 2) LOAD NAVIGATION BUTTON IMAGE
    # ----------------------------------------------------------------
    nav_button_path = os.path.join(
        os.path.dirname(__file__),
        "iconsAndImages",
        "NavigationButton.png"
    )

    if not os.path.exists(nav_button_path):
        messagebox.showerror("Error", f"Navigation button image not found: {nav_button_path}")
        root.destroy()
        return

    nav_button_image = Image.open(nav_button_path)
    original_width, original_height = nav_button_image.size
    resized_nav_button = nav_button_image.resize((original_width // 2, original_height // 2))
    nav_button_image_tk = ImageTk.PhotoImage(resized_nav_button)

    # ----------------------------------------------------------------
    # 3) CUSTOM DROPDOWN POPUP USING A TOGGLE APPROACH
    # ----------------------------------------------------------------
    dropdown_popup = None
    dropdown_options = ["System View", "Alarm View", "About"]

    def create_dropdown_popup():
        """Toggle showing a custom dropdown popup just under the main button."""
        nonlocal dropdown_popup

        # If a popup already exists, destroy it (toggle behavior)
        if dropdown_popup is not None:
            dropdown_popup.destroy()
            dropdown_popup = None
            return

        # Coordinates of the main button (place the popup just below it)
        x_coord = nav_button.winfo_rootx()
        y_coord = nav_button.winfo_rooty() + nav_button.winfo_height()

        # Create a Toplevel for the custom dropdown
        dropdown_popup = tk.Toplevel(root)
        dropdown_popup.configure(bg="#063028")
        dropdown_popup.overrideredirect(True)  # Remove window decorations
        dropdown_popup.geometry(f"+{x_coord}+{y_coord}")

        # Create a button for each option
        for option_label in dropdown_options:
            # Each "option" is styled like the main nav button
            option_btn = tk.Button(
                dropdown_popup,
                text=option_label,
                image=nav_button_image_tk,  # Use the same nav button image
                compound="center",          # Text centered on top of the image
                font=("Helvetica", 16, "bold"),
                fg="white",
                bg="#063028",
                activebackground="#063028",
                bd=0,
                relief="flat",
                highlightthickness=0,
                highlightbackground="#063028",
                highlightcolor="#063028",
                command=lambda opt=option_label: on_dropdown_select(opt)
            )
            option_btn.image = nav_button_image_tk  # Keep reference
            option_btn.pack(pady=2)

    def on_dropdown_select(selected_option):
        """Handle selection of a dropdown option."""
        print(f"Selected: {selected_option}")
        # Close the popup
        if dropdown_popup:
            dropdown_popup.destroy()

    # ----------------------------------------------------------------
    # 4) MAIN "NAVIGATION" BUTTON
    # ----------------------------------------------------------------
    nav_button = tk.Button(
        root,
        text="Navigation",
        image=nav_button_image_tk,
        compound="center",
        font=("Helvetica", 16, "bold"),
        fg="white",
        bg="#063028",
        activebackground="#063028",
        bd=0,
        relief="flat",
        highlightthickness=0,
        highlightbackground="#063028",
        highlightcolor="#063028",
        command=create_dropdown_popup  # Show/hide the dropdown on click
    )
    nav_button.place(x=200, y=200)
    nav_button.image = nav_button_image_tk

    root.mainloop()

if __name__ == "__main__":
    main()

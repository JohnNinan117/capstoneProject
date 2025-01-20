import tkinter as tk

def main():
    root = tk.Tk()
    root.title("Battery Management System")
    root.geometry("1280x720")
    root.configure(bg="#063028")

    image = tk.PhotoImage(
        file="/Users/johnninan/Documents/GitHub/capstoneProject/iconsAndImages/battery (8).png"
    )

    # Create a frame at the bottom
    bottom_frame = tk.Frame(root, bg="#063028")
    bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)  # pady=20 pushes the frame up

    # Pack the label to the LEFT side of the bottom_frame
    label = tk.Label(bottom_frame, image=image, bg="#063028")
    label.pack(side=tk.LEFT, padx=20, pady=20)  # side=tk.LEFT positions it on the left

    # Keep a reference so the image isn’t garbage-collected        
    label.image = image

    root.mainloop()

if __name__ == "__main__":
    main()

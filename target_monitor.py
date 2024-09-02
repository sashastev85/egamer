import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, Toplevel
import threading
import numpy as np
import cv2
import pyautogui
import pygetwindow as gw
import win32gui
import win32con
from PIL import Image, ImageTk
import time

# Global variables
target_image = None
target_image_gray = None
running = False
screen_region = None
orb = cv2.ORB_create()  # ORB detector

def load_image():
    global target_image, target_image_gray, kp_target, des_target
    file_path = filedialog.askopenfilename(filetypes=[("JPEG files", "*.jpg")])
    if file_path:
        target_image = cv2.imread(file_path)
        target_image_gray = cv2.cvtColor(target_image, cv2.COLOR_BGR2GRAY)
        
        # Detect keypoints and descriptors for the target image
        kp_target, des_target = orb.detectAndCompute(target_image_gray, None)

        img = Image.open(file_path)
        img.thumbnail((200, 200))
        img = ImageTk.PhotoImage(img)
        img_label.config(image=img)
        img_label.image = img
        start_button.config(state="normal")
        log_message("Target image loaded.")

def select_screen_area():
    # Create a transparent fullscreen window
    top = Toplevel(root)
    top.attributes("-alpha", 0.3)  # Set transparency
    top.attributes("-fullscreen", True)  # Fullscreen mode

    canvas = tk.Canvas(top, cursor="cross")
    canvas.pack(fill=tk.BOTH, expand=True)

    def on_press(event):
        global start_x, start_y
        start_x, start_y = event.x, event.y  # Save the initial positions
        canvas.create_rectangle(start_x, start_y, start_x + 1, start_y + 1, outline='red', tag='selection')

    def on_drag(event):
        # Update the rectangle as the mouse is dragged
        canvas.coords('selection', start_x, start_y, event.x, event.y)

    def on_release(event):
        # Save the final coordinates and close the transparent window
        global screen_region
        screen_region = (start_x, start_y, event.x, event.y)
        top.destroy()
        log_message(f"Screen area selected: {screen_region}")

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)

def start_monitoring():
    global running, match_count
    if screen_region is None:
        messagebox.showerror("Error", "Please select a screen area first.")
        return
    running = True
    match_count = int(match_count_var.get())
    status_button.config(bg="green", text="Running")
    log_message("Monitoring started.")
    monitor_thread = threading.Thread(target=monitor_screen)
    monitor_thread.start()

def stop_monitoring():
    global running
    running = False
    status_button.config(bg="red", text="Stopped")
    log_message("Monitoring stopped.")

def monitor_screen():
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    while running:
        screen = pyautogui.screenshot(region=screen_region)
        screen_np = np.array(screen)
        screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_BGR2GRAY)

        # Detect keypoints and descriptors in the screen
        kp_screen, des_screen = orb.detectAndCompute(screen_gray, None)

        # Match descriptors
        matches = bf.match(des_target, des_screen)
        matches = sorted(matches, key=lambda x: x.distance)

        # If a sufficient number of matches are found, trigger the action
        if len(matches) > 10:  # Adjust this threshold as needed
            log_message(f"Target spotted ({len(matches)} matches found)")
            bring_game_window_to_foreground()
            pyautogui.press("space")  # Simulate spacebar press
            time.sleep(0.1)  # Slight delay to ensure keypress is registered
            break

        log_message("Scanning screen...")

def bring_game_window_to_foreground():
    window_title = 'Lucky 88'  # Replace with your game window title
    try:
        # First attempt to bring the window to the foreground using pygetwindow
        game_window = gw.getWindowsWithTitle(window_title)[0]
        game_window.activate()
    except IndexError:
        # If pygetwindow fails, use win32gui as a fallback method
        hwnd = win32gui.FindWindow(None, window_title)
        if hwnd:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)  # Restore window if minimized
            win32gui.SetForegroundWindow(hwnd)
        else:
            log_message("Game window not found. Ensure the game is running and the title is correct.")

def log_message(message):
    log_screen.insert(tk.END, message + "\n")
    log_screen.see(tk.END)

root = tk.Tk()
root.title("Target Monitor")

frame_left = tk.Frame(root)
frame_left.pack(side=tk.LEFT, padx=10, pady=10)

frame_right = tk.Frame(root)
frame_right.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)

upload_button = tk.Button(frame_left, text="Upload Target Image", command=load_image)
upload_button.pack(pady=10)

img_label = tk.Label(frame_left)
img_label.pack(pady=10)

match_count_var = tk.StringVar(value="1")
match_count_label = tk.Label(frame_left, text="How many targets before activation?")
match_count_label.pack(pady=5)
match_count_entry = tk.Entry(frame_left, textvariable=match_count_var)
match_count_entry.pack(pady=5)

status_button = tk.Button(frame_left, text="Stopped", bg="red", state="disabled")
status_button.pack(pady=10)

start_button = tk.Button(frame_left, text="Start", state="disabled", command=start_monitoring)
start_button.pack(pady=10)

stop_button = tk.Button(frame_left, text="Stop", command=stop_monitoring)
stop_button.pack(pady=10)

select_area_button = tk.Button(frame_left, text="Select Screen Area", command=select_screen_area)
select_area_button.pack(pady=10)

log_screen = scrolledtext.ScrolledText(frame_right, wrap=tk.WORD, width=60, height=20, state='normal')
log_screen.pack(pady=10, padx=10)

root.mainloop()

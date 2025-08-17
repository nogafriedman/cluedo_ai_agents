from tkinter import Tk, Toplevel, Label
import time

class PopupManager:
    def __init__(self, root):
        self.root = root
        self.popup_queue = []
        self.popup_active = False

    def show_popup(self, message, delay=2000):
        # Add the popup to the queue
        self.popup_queue.append((message, delay))
        if not self.popup_active:
            self.process_next_popup()

    def process_next_popup(self):
        if self.popup_queue:
            message, delay = self.popup_queue.pop(0)
            self.popup_active = True
            self.create_popup(message)
            self.root.after(delay, self.close_popup)

    def create_popup(self, message):
        self.popup_window = Toplevel(self.root)
        # self.popup_window.geometry("300x100")
        Label(self.popup_window, text=message, font=("Arial", 14)).pack(pady=20)

    def close_popup(self):
        if self.popup_window:
            self.popup_window.destroy()
            self.popup_active = False
            self.process_next_popup()  # Process the next popup after closing the current one

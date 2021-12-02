import tkinter as tk
from tkinter import *
from tkinter import filedialog, ttk
from PIL import ImageTk, Image, ImageDraw


class CanvasBee:

    def __init__(self, content):
        self.canvas = Canvas(content, width=960, height=600, borderwidth=5)
        self.photo = Image.open(r'icons/blank_image.png')
        self.photo = self.photo.resize((960, 600), Image.ANTIALIAS)
        self.photo = ImageTk.PhotoImage(image=self.photo)
        self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

    def insert_image_in_Canvas(self, image_path):
        self.photo = Image.open(image_path)
        self.photo = self.photo.resize((960, 600), Image.ANTIALIAS)
        self.photo = ImageTk.PhotoImage(image=self.photo)
        self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

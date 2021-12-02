import tkinter as tk
from tkinter import *
from tkinter import filedialog, ttk

class OptionsHough:

    """
    def __init__(self, minRadius = 25, maxRadius = 45, param1 = 80, param2 = 35, minArea = 300, boundingBoxMinArea = 500, scale = 0, cameraHeight = 0):
        self.minRadius = minRadius
        self.maxRadius = maxRadius
        self.param1 = param1
        self.param2 = param2
        self.minArea = minArea
        self.boundingBoxMinArea = boundingBoxMinArea
        self.scale = scale
        self.cameraHeight = cameraHeight"""


    def __init__(self):
        self.minRadius = StringVar(value="25")
        self.maxRadius = StringVar(value="45")
        self.param1 = StringVar(value="80")
        self.param2 = StringVar(value="35")
        #self.minArea = StringVar(value="300")
        #self.boundingBoxMinArea = StringVar(value="500")
        self.mediumCellSize = StringVar(value="180")
        self.scale = DoubleVar(value=0.59) #micronsPerPixel
        self.cameraHeight = IntVar(value=10)
        self.diluent = IntVar(value=0)

    def reset_options(self):
        self.minRadius.set("25")
        self.maxRadius.set("45")
        self.param1.set("80")
        self.param2.set("35")
        #self.minArea.set("300")
        #self.boundingBoxMinArea.set("500")
        self.mediumCellSize.set("180")
        self.scale.set(0.59)
        self.cameraHeight.set(10)
        self.diluent.set(0)

    def return_options(self):
        return(int(self.minRadius.get()),
                                       int(self.maxRadius.get()),
                                       int(self.param1.get()),
                                       int(self.param2.get()),
                                       int(self.mediumCellSize.get()),
                                       float(self.scale.get()),
                                       int(self.cameraHeight.get()),
                                       int(self.diluent.get())
                                       )
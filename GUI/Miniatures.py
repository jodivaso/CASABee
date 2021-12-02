import tkinter as tk
from tkinter import *
from tkinter import ttk
from PIL import ImageTk, Image
from Domain.Video import VideoAnalyzer
from Domain.Utils import *
from pathlib import Path
import cv2 as cv


class Miniatures():

    def __init__(self, content, canvas, options, resultsString, editing, videoInfoText):
        # LAS MINIATURAS DE IMAGENES
        # Create a frame for the canvas with non-zero row&column weights
        self.content=content
        self.frame_canvas = tk.Frame(content)
        self.frame_canvas.grid(row=1, column=0, pady=(5, 0), padx=(5,0), sticky='nw')
        self.frame_canvas.grid_rowconfigure(0, weight=1)
        self.frame_canvas.grid_columnconfigure(0, weight=1)
        # Set grid_propagate to False to allow 5 miniatures resizing later
        self.frame_canvas.grid_propagate(False)

        # Add a canvas in that frame
        self.toolbarSelection = Canvas(self.frame_canvas)
        self.toolbarSelection.grid(row=0, column=0, sticky="news")

        # Link a scrollbar to the canvas
        self.hsb = tk.Scrollbar(self.frame_canvas, orient="horizontal", command=self.toolbarSelection.xview)
        self.hsb.grid(row=1, column=0, sticky='we')
        self.toolbarSelection.configure(xscrollcommand=self.hsb.set)

        # Create a frame to contain the miniatures
        self.frame_buttons = tk.Frame(self.toolbarSelection)
        self.toolbarSelection.create_window((0, 0), window=self.frame_buttons)
        self.miniatures = []

        self.CanvasBee = canvas
        #self.photo = photo

        self.list_videos = []
        self.current_video_name = ""

        self.stop_video=False

        self.options = options
        self.resultsString = resultsString
        self.videoInfoText = videoInfoText

        self.editing = editing
        self.cap=None


    def getOutputVideoName(self, video_name):
        i = video_name.rindex("/")
        return video_name[:i] + "/Output/"+video_name[i+1:]

    #Cuando cambio de miniatura, para que muestre las opciones con las que se analizó el video.
    def printCurrentOptions(self, v):
        self.options.minRadius.set(v.minRadius)
        self.options.maxRadius.set(v.maxRadius)
        self.options.param1.set(v.param1)
        self.options.param2.set(v.param2)
        self.options.mediumCellSize.set(v.mediumCellSize)
        self.options.scale.set(v.micronsPerPixel)
        self.options.cameraHeight.set(v.cameraDepth)
        self.options.diluent.set(v.diluent)


    def analyze_video(self, video_name, show_analyzing_image):
        self.current_video_name = video_name
        if video_name in [x.file_path for x in self.list_videos]:
            v = next(x for x in self.list_videos if
                     x.file_path == video_name)  # Si existia el video en la lista de videos, entonces lo pillo
            self.printCurrentOptions(v) #Y actualizo las opciones con las que se analizó.
        else:
            v = VideoAnalyzer(video_name, self.resultsString)
            self.list_videos.append(v)
            if show_analyzing_image:
                self.CanvasBee.insert_image_in_Canvas(r"icons/analyzing_image.png")
            self.CanvasBee.canvas.update()
            v.videoSpermDetection(self.options.return_options())
            """
            background = np.array(miniature.image)
            background = cv.cvtColor(background, cv.COLOR_BGR2GRAY)
            overlay = cv.imread('icons/green_check.png')
            added_image = cv.addWeighted(background, 0.4, overlay, 0.1, 0)
            im = Image.fromarray(added_image)
            im = im.resize((72 * 2, 72), Image.ANTIALIAS)
            img = ImageTk.PhotoImage(image=im)
            miniature.configure(image=img)"""
        self.CanvasBee.canvas.update()
        v.getResults()  # Para actualizar los resultados en el cuadro de texto del GUI.
        return v

    def pressButtonMiniature(self, video_name, miniature):
        self.CanvasBee.canvas.delete("all") #Para borrar todo lo que tenga el canvas.

        self.editing.edit_mode = False
        self.stop_video = True
        v = self.analyze_video(video_name, True)

        #Al pulsar el botón, pongo en verde el texto para que se sepa que se ha procesado
        i = self.miniatures.index(miniature) + 1
        img_green = Utils.img_frame_miniature_with_text(video_name, index=i, fontColor=(0, 128, 0))
        miniature.configure(image=img_green)
        miniature.image=img_green
        if v.update_required: #Si hace falta actualizar (porque se han hecho cambios al editar)
            v.updateVideo()
            v.update_required = False

        #Pongo la información del vídeo
        self.videoInfoText.set(self.getVideoInfo(video_name))

        self.stop_video = False
        self.cap = cv.VideoCapture(v.outputVideo)
        self.PlayVideo()

    def getVideoInfo(self, video_name):
        file_paths = [x.file_path for x in self.list_videos]
        number_video = file_paths.index(video_name) + 1
        videoName = Path(self.current_video_name).stem
        return "Video number: " + str(number_video) + "\n" + "Video name: " + videoName

    def PlayVideo(self):
        #cap = cv.VideoCapture(file_name)
        success, frame = self.cap.read()
        while success and not self.stop_video:
            cv2image = cv.cvtColor(frame, cv.COLOR_BGR2RGBA)
            img = Image.fromarray(cv2image)
            img = img.resize((960, 600), Image.ANTIALIAS)
            imgtk = ImageTk.PhotoImage(image=img)
            self.CanvasBee.canvas.create_image(0, 0, image=imgtk, anchor=tk.NW)
            self.CanvasBee.photo = imgtk
            self.CanvasBee.canvas.update()
            success, frame = self.cap.read()
        if self.stop_video or not success:
            self.cap.release()
        if not self.stop_video and success:
            self.PlayVideo()



    def deleteMiniatures(self):
        for widgets in self.frame_buttons.winfo_children():
            widgets.destroy()
        self.miniatures=[]
        self.list_videos = []
        self.current_video_name = ""

    def addMiniature(self, img,video_name):
        miniature = ttk.Button(self.frame_buttons)
        miniature.configure(image=img, command = lambda: self.pressButtonMiniature(video_name, miniature))
        miniature.image = img
        miniature.grid(row=0, column=len(self.miniatures))
        self.miniatures.append(miniature)

    def config_scroll(self):
        self.frame_buttons.update_idletasks()

        # Resize the canvas frame to show exactly 5 miniatures and the scrollbar
        number_displayed_miniatures = len(self.miniatures) if len(self.miniatures)<5 else 5
        first5columns_width = sum([self.miniatures[i].winfo_width() for i in range(0, number_displayed_miniatures)])
        self.frame_canvas.config(width=first5columns_width,
                                 height=self.miniatures[0].winfo_height() + self.hsb.winfo_height())

        # Set the canvas scrolling region
        if number_displayed_miniatures<5:
            self.hsb.grid_forget()
        else:
            self.hsb.grid(row=1, column=0, sticky='we')
        self.hsb.update()
        self.content.update()
        self.toolbarSelection.config(scrollregion=self.toolbarSelection.bbox("all"))

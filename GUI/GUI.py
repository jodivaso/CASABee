import tkinter as tk
from tkinter import *
from tkinter import filedialog, ttk, simpledialog

from GUI.CanvasBee import CanvasBee
from GUI.Miniatures import Miniatures

from Domain.OptionsHough import OptionsHough
from Domain.Utils import *
from Domain.EditMode import *
import copy
import multiprocessing
import os


class App():

    def __init__(self):
        self.draw_contour = []
        self.state_drawing_contour = False
        self.id_temp_contour = None
        self.double_click_flag = False

        self.centers_and_circles = []
        self.contours = []

        self.state_drawing_circle = False
        self.state_moving_circle = False
        self.index_circle = -1
        # self.style = Style('yeti')
        # self.style = Style()
        # self.style.theme_use('minty')

        self.root = tk.Tk()
        self.root.title("CASABee")
        if "nt" == os.name:
            self.root.iconbitmap(r"icons/Bee.ico")

        self.options = OptionsHough()

        self.time_required = DoubleVar()

        self.state_analysing = StringVar(value="Finished!")

        self.analyze_all = False
        self.editing = EditMode()

        self.resultsString = StringVar(value="No results currently")
        self.videoInfoText = StringVar(value="No video selected")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.content = tk.Frame(self.root)

        self.printGUI()
        self.root.mainloop()

    def draw_circles_from_openCV_to_GUI(self, detected_circles):
        self.centers_and_circles = []
        xs = [(x // 2, y // 2, r // 2) for (x, y, r) in detected_circles]
        for (x, y, r) in xs:
            # Draw the center
            id_center = self.CanvasBee.canvas.create_oval(x - 1, y - 1, x + 1, y + 1, width=1, outline="red")
            # Draw the circle
            id_circle = self.CanvasBee.canvas.create_oval(x - r, y - r, x + r, y + r, width=4, outline="green")
            # Add them to the list of centers and circles
            self.centers_and_circles.append((id_center, id_circle))

    def draw_contours_from_openCV_to_GUI(self, contours):  # TODO: ESTO SE TIENE QUE HACER MEJOR, ES MUY PESADO
        xs = []
        for (a, n) in contours:  # Cada contorno
            ys = []
            for x in a:  # Cada punto
                # i=0
                # if (i%7==0): #IMPORTANT: Dibujo uno de cada 7 puntos, por eficiencia después para procesarlos.
                ys.append([x[0][0] // 2, x[0][1] // 2])
                # i+=1
            xs.append((ys, n))
        self.contours = []
        for (a, n) in xs:
            ys = []
            x_max = 0
            y_max = 0
            for punto in a:
                x = punto[0]
                y = punto[1]
                id_point = self.CanvasBee.canvas.create_line(x, y, x + 1, y, fill='red', width=4,
                                                             state="hidden")  # Los pongo ocultos
                ys.append(id_point)
                if x > x_max:  # Me guardo el punto con mayor x, para dibujar el número
                    x_max = x
                    y_max = y
                if y_max < 10:  # Si el y está demasiado arriba, no se vería, así que lo bajo un poco
                    y_max = 20
                if x_max < 50:
                    x_max = 65  # Si el x está demasiado a la izquierda, no se vería, así que lo separo un poco
            flattened = [p for x in a for p in x]  # Creo la lista de puntos aplanada
            id_contour = self.CanvasBee.canvas.create_line(*flattened, fill='red', width=4,
                                                           smooth=1)  # Dibujo así el contorno
            id_text = self.CanvasBee.canvas.create_text(x_max - 50, y_max, text=n, fill="magenta",
                                                        font=('Helvetica 15 bold'))
            self.contours.append((id_contour, ys,
                                  id_text))  # Un contorno es una tripla (id_contorno, [id_punto1, id_punto2, ... , id_puntoN], id_number)

    def printGUI(self):

        self.content.grid(column=0, row=0)

        self.CanvasBee = CanvasBee(self.content)
        self.CanvasBee.canvas.grid(column=0, row=3, rowspan=3)  # Que ocupe tres filas el canvas

        videoInfo = ttk.Labelframe(self.content, text="Video Information")
        videoInfo.grid(row=3, column=1, sticky='NWES', padx=10)
        videoInfoLabel = ttk.Label(videoInfo, textvariable=self.videoInfoText)
        videoInfoLabel.grid(sticky="NWES")

        options = ttk.Labelframe(self.content, text="Options")
        results = ttk.Labelframe(self.content, text="Results")

        options.grid(row=4, column=1, sticky='NWES', padx=10)
        results.grid(row=5, column=1, sticky='WENS', padx=10, pady=10)

        # La parte de las opciones

        minRadiusLabel = ttk.Label(options, text="MinRadius")
        minRadiusSpinbox = ttk.Spinbox(options, from_=1.0, to=50.0, increment=1.0, textvariable=self.options.minRadius)

        maxRadiusLabel = ttk.Label(options, text="MaxRadius")
        maxRadiusSpinbox = ttk.Spinbox(options, from_=1.0, to=50.0, increment=1.0, textvariable=self.options.maxRadius)

        param1Label = ttk.Label(options, text="Param1")
        param1Spinbox = ttk.Spinbox(options, from_=1.0, to=100.0, increment=1.0, textvariable=self.options.param1)

        param2Label = ttk.Label(options, text="Param2")
        param2Spinbox = ttk.Spinbox(options, from_=1.0, to=100.0, increment=1.0, textvariable=self.options.param2)

        analyzingStatusLabel = ttk.Label(options, textvar=self.state_analysing)

        timeRequiredLabel = ttk.Label(options, textvar=self.time_required)
        timeRequiredLabelText = ttk.Label(options, text="Time required (s)")

        self.progressbar = ttk.Progressbar(options, length=100, mode="indeterminate")

        analyzeButton = ttk.Button(options, text="Analyze", command=lambda: self.analyze_and_show(),
                                   padding=10)

        separator1 = ttk.Separator(options, orient=HORIZONTAL)

        mediumCellSizeLabel = ttk.Label(options, text="Medium cell size")
        mediumCellSizeSpinBox = ttk.Spinbox(options, from_=200.0, to=400.0, increment=10.0,
                                            textvariable=self.options.mediumCellSize)
        # boundingBoxMinAreaLabel = ttk.Label(options, text="BoundingBox MinArea")
        # boundingBoxMinAreaSpinBox = ttk.Spinbox(options, from_=400.0, to=650.0, increment=10.0,
        #                                        textvariable=self.options.boundingBoxMinArea)

        separator2 = ttk.Separator(options, orient=HORIZONTAL)

        scaleLabel = ttk.Label(options, text="Scale (\u03BCm/pixel)")
        scaleLabelSpinBox = ttk.Spinbox(options, from_=0.0, to=10.0, increment=0.01, textvariable=self.options.scale)

        separator3 = ttk.Separator(options, orient=HORIZONTAL)

        cameraHeightLabel = ttk.Label(options, text="Camera height (\u03BCm)")
        cameraHeightSpinBox = ttk.Spinbox(options, from_=0.0, to=100.0, increment=0.5, textvariable=self.options.cameraHeight)

        separator4 = ttk.Separator(options, orient=HORIZONTAL)

        dilutionLabel = ttk.Label(options, text="Diluent parts")
        dilutionSpinBox = ttk.Spinbox(options,from_=0.0, to=50.0, increment=1, textvariable=self.options.diluent)

        minRadiusLabel.grid(row=0, column=0)
        minRadiusSpinbox.grid(row=0, column=1)
        maxRadiusLabel.grid(row=1, column=0)
        maxRadiusSpinbox.grid(row=1, column=1)
        param1Label.grid(row=2, column=0)
        param1Spinbox.grid(row=2, column=1)
        param2Label.grid(row=3, column=0)
        param2Spinbox.grid(row=3, column=1)

        separator1.grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

        mediumCellSizeLabel.grid(row=5, column=0)
        mediumCellSizeSpinBox.grid(row=5, column=1)
        # boundingBoxMinAreaLabel.grid(row=6, column=0)
        # boundingBoxMinAreaSpinBox.grid(row=6, column=1)

        separator2.grid(row=7, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

        scaleLabel.grid(row=8, column=0)
        scaleLabelSpinBox.grid(row=8, column=1)
        cameraHeightLabel.grid(row=9, column=0)
        cameraHeightSpinBox.grid(row=9, column=1)

        separator3.grid(row=10, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

        #self.progressbar.grid(row=12, column=1, sticky="ew")
        #analyzingStatusLabel.grid(row=12, column=0)

        #timeRequiredLabel.grid(row=13, column=1)
        #timeRequiredLabelText.grid(row=13, column=0, sticky="w")

        dilutionLabel.grid(row=11, column=0)
        dilutionSpinBox.grid(row=11, column=1)

        separator4.grid(row=12, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

        analyzeButton.grid(row=13, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

        resultsLabel = ttk.Label(results, textvariable=self.resultsString)
        resultsLabel.grid()

        toolbar = ttk.Frame(self.content)

        toolbar.grid(row=0, column=0, sticky="W", padx=10)

        """
        openImage = Image.open(r'icons/open-image.png')
        openImage = openImage.resize((72, 72), Image.ANTIALIAS)
        openImage = ImageTk.PhotoImage(openImage)
        openImageButton = ttk.Button(toolbar, image=openImage, style='flat.TButton', command=self.selecting_file)
        openImageButton.image = openImage
        """

        openVideo = Image.open(r'icons/open-video.png')
        openVideo = openVideo.resize((72, 72), Image.ANTIALIAS)
        openVideo = ImageTk.PhotoImage(openVideo)
        openVideoButton = ttk.Button(toolbar, image=openVideo, style='flat.TButton', command=self.selecting_videos)
        openVideoButton.image = openVideo

        saveImg = Image.open(r'icons/save.png')
        saveImg = saveImg.resize((72, 72), Image.ANTIALIAS)
        saveImg = ImageTk.PhotoImage(saveImg)
        saveButton = ttk.Button(toolbar, image=saveImg, style='flat.TButton')
        saveButton.image = saveImg

        export = Image.open(r'icons/export.png')
        export = export.resize((72, 72), Image.ANTIALIAS)
        export = ImageTk.PhotoImage(export)
        exportButton = ttk.Button(toolbar, image=export, style='flat.TButton', command=self.export_csv)
        exportButton.image = export

        reset = Image.open(r'icons/reset.png')
        reset = reset.resize((72, 72), Image.ANTIALIAS)
        reset = ImageTk.PhotoImage(reset)
        resetButton = ttk.Button(toolbar, image=reset, style='flat.TButton', command=self.reset)
        resetButton.image = reset

        # saveVideos = Image.open(r'icons/save_video.png')
        # saveVideos = saveVideos.resize((72, 72), Image.ANTIALIAS)
        # saveVideos = ImageTk.PhotoImage(saveVideos)
        # saveVideosButton = ttk.Button(toolbar, image=saveVideos, style='flat.TButton')
        # saveVideosButton.image = saveVideos

        editIcon = Image.open(r'icons/edit icon.png')
        editIcon = editIcon.resize((72, 72), Image.ANTIALIAS)
        editIcon = ImageTk.PhotoImage(editIcon)
        editButton = ttk.Button(toolbar, image=editIcon, style='flat.TButton', command=self.edit_mode)
        editButton.image = editIcon

        # openImageButton.grid(row=0, column=0)
        openVideoButton.grid(row=0, column=0)
        # saveButton.grid(row=0, column=1)
        resetButton.grid(row=0, column=2)
        exportButton.grid(row=0, column=3)
        # saveVideosButton.grid(row=0, column=4)
        editButton.grid(row=0, column=5)

        self.miniatures = Miniatures(self.content, self.CanvasBee, self.options, self.resultsString, self.editing,
                                     self.videoInfoText)

        self.CanvasBee.canvas.bind("<ButtonPress-1>", self.mouse_click)
        self.CanvasBee.canvas.bind('<B1-Motion>', lambda event: self.B1Motion_handler(event))
        self.CanvasBee.canvas.bind('<ButtonRelease-1>', lambda event: self.mouse_click_release(event))
        self.CanvasBee.canvas.bind('<Button-3>', self.delete_circle)
        self.CanvasBee.canvas.bind_all('<KeyPress-h>', self.hide)
        self.CanvasBee.canvas.bind_all('<KeyRelease-h>', self.unhide)
        self.CanvasBee.canvas.bind("<Motion>", self.motion_handler)
        self.CanvasBee.canvas.bind('<Double-Button-1>', self.mouse_double_click)
        self.CanvasBee.canvas.bind_all('<Control-Key-z>', self.undo)



        self.root.protocol('WM_DELETE_WINDOW', self.on_closing)

    def on_closing(self):
        self.miniatures.stop_video = True
        self.root.destroy()

    def analyze_all_window(self, number_videos):
        self.analyze_all = tk.messagebox.askyesno("Question",
                                                  "You selected " + str(
                                                      number_videos) + " videos.\n\nDo you want to analyze all of them now?",
                                                  icon='question')

    def selecting_videos(self):
        self.file_paths_videos = filedialog.askopenfilenames(filetypes=[("Video files", "*.avi")])
        self.stopVideo()

        # mp = MediaPlayer(self.content)

        if len(self.file_paths_videos) > 0:  # Para tratar el caso de que pulsen cancelar
            self.reset()  # Reseteamos lo que ubiese
            # Dibujo los videos seleccionados
            i = 1
            self.miniatures.deleteMiniatures()

            for video_name in self.file_paths_videos:
                # Creo la imagen (un frame + texto "Video X").
                img = Utils.img_frame_miniature_with_text(video_name, index=i, fontColor=(255, 255, 255))
                # Creo los buttons con las miniaturas
                self.miniatures.addMiniature(img, video_name)
                i += 1

            self.miniatures.config_scroll()
            self.analyze_all_window(len(self.file_paths_videos))  # Pregunto si quiero que se analicen todos los videos
            if self.analyze_all:  # Si se ha marcado que sí, entonces procedo a analizar.
                self.CanvasBee.insert_image_in_Canvas(r"icons/Analyzing_videos.png")
                i = 0
                for video_name in self.file_paths_videos:
                    self.miniatures.analyze_video(video_name, show_analyzing_image=False)  # Analizo
                    # Y pinto en verde el texto de la miniature una vez analizado.
                    miniature = self.miniatures.miniatures[i]
                    img_green = Utils.img_frame_miniature_with_text(video_name, index=i + 1, fontColor=(0, 128, 0))
                    miniature.configure(image=img_green)
                    miniature.image = img_green
                    i += 1
                self.CanvasBee.insert_image_in_Canvas(r"icons/Analysis_finished.png")

    # FUNCIONES

    def stopVideo(self):
        self.miniatures.stop_video = True

    def analyze_and_show(self):
        self.CanvasBee.canvas.delete("all")
        self.editing.edit_mode = False
        v = next(x for x in self.miniatures.list_videos if
                 x.file_path == self.miniatures.current_video_name)  # Pillo el videoAnalyzer correspondiente

        if (int(self.options.minRadius.get()) == v.minRadius
                and int(self.options.maxRadius.get()) == v.maxRadius
                and int(self.options.param1.get()) == v.param1
                and int(self.options.param2.get()) == v.param2
                and int(self.options.mediumCellSize.get()) == v.mediumCellSize
                and self.options.scale.get() == v.micronsPerPixel):
            #Si todos eran iguales, entonces simplemente asigno los nuevos valores de la camara y el diluyente (no hace falta recalcular el video)
            v.cameraDepth = self.options.cameraHeight.get()
            v.diluent = self.options.diluent.get()
        else: #Si alguno es distinto, entonces hay que recalcular el video
            self.CanvasBee.photo = Image.open(r'icons/analyzing_image.png')
            self.CanvasBee.photo = self.CanvasBee.photo.resize((960, 600), Image.ANTIALIAS)
            self.CanvasBee.photo = ImageTk.PhotoImage(image=self.CanvasBee.photo)
            self.CanvasBee.canvas.create_image(0, 0, image=self.CanvasBee.photo, anchor=tk.NW)
            self.CanvasBee.canvas.update()
            v.videoSpermDetection(self.options.return_options())

        self.CanvasBee.canvas.update()
        v.getResults()  # Para actualizar los resultados en el cuadro de texto del GUI.
        self.miniatures.stop_video = False
        if self.miniatures.cap is not None:
            self.miniatures.cap.release()
        self.miniatures.cap = cv.VideoCapture(v.outputVideo)
        self.miniatures.PlayVideo()

    # EVENTOS:

    def hide(self, event):
        if self.editing.edit_mode:  # Solo si estamos en el modo de edición
            for (id_center, id_circle) in self.centers_and_circles:
                self.CanvasBee.canvas.itemconfig(id_center, state='hidden')
                self.CanvasBee.canvas.itemconfig(id_circle, state='hidden')
            for (id_contour, list_id_points, id_number) in self.contours:
                self.CanvasBee.canvas.itemconfig(id_contour, state='hidden')
                # for id_point in list_id_points:
                #    self.CanvasBee.canvas.itemconfig(id_point, state='hidden')
                self.CanvasBee.canvas.itemconfig(id_number, state='hidden')

    def unhide(self, event):
        if self.editing.edit_mode:  # Solo si estamos en el modo de edición
            for (id_center, id_circle) in self.centers_and_circles:
                self.CanvasBee.canvas.itemconfig(id_center, state='normal')
                self.CanvasBee.canvas.itemconfig(id_circle, state='normal')
            for (id_contour, list_id_points, id_number) in self.contours:
                self.CanvasBee.canvas.itemconfig(id_contour, state='normal')
                # for id_point in contour:
                #    self.CanvasBee.canvas.itemconfig(id_point, state='normal')
                self.CanvasBee.canvas.itemconfig(id_number, state='normal')

    def mouse_click(self, event):
        self.root.after(300, self.mouse_action, event)

    def mouse_double_click(self, event):
        self.double_click_flag = True

    def mouse_action(self, event):
        if self.editing.edit_mode:
            if self.double_click_flag:
                self.double_click_flag = False
                self.Double_Button1_handler(event)
            else:
                self.ButtonPress1_handler(event)

    def ButtonPress1_handler(self, event):  # MOVE OR DRAW
        if self.editing.edit_mode:
            if self.state_drawing_contour:
                self.draw_contour.append((event.x, event.y))
                flattened = [a for x in self.draw_contour for a in x]
                if len(flattened) > 2:
                    if self.id_temp_contour is not None:
                        self.CanvasBee.canvas.delete(self.id_temp_contour)
                    flattened = [a for x in self.draw_contour for a in x]
                    self.id_temp_contour = self.CanvasBee.canvas.create_line(*flattened, smooth=1, fill="yellow",
                                                                             width=2)
            else:
                self.save_actual_state() #Me guardo tal y como lo tengo ahora (antes de cambiar número/modificar/mover)
                changed_number = False
                # Si estoy sobre un número, puedo editarlo el número
                for (contour, list_points, id_number) in self.contours:
                    x, y, = self.CanvasBee.canvas.coords(id_number)
                    if (x <= event.x + 10 and x >= event.x - 10 and y >= event.y - 10 and y <= event.y + 10):
                        n = self.CanvasBee.canvas.itemcget(id_number, 'text')
                        number = simpledialog.askinteger("Number of contours?",
                                                         "Please enter the correct number of contours (current " + str(
                                                             n) + ")",
                                                         parent=self.content, minvalue=0, maxvalue=35)
                        self.CanvasBee.canvas.itemconfig(id_number, text=number)
                        changed_number = True
                        # Modifico el número en la lista de OpenCV
                        self.modify_number_contour_opencv_list(contour, list_points, id_number)

                # Si no he cambiado ningún número, significa que voy a añadir un círculo o moverlo
                if not changed_number:
                    for index, (id_center, id_circle) in enumerate(self.centers_and_circles):  # MOVE
                        x, y, _, _ = self.CanvasBee.canvas.coords(id_center)
                        if (x <= event.x + 10 and x >= event.x - 10 and y >= event.y - 10 and y <= event.y + 10):
                            self.state_moving_circle = True
                            self.start_move_circle2(event, id_center, id_circle)
                            self.index_circle = index
                            break
                    if not self.state_moving_circle:  # DRAW
                        self.state_drawing_circle = True
                        self.draw_center2(event)

    def B1Motion_handler(self, event):  # MOVE OR DRAW
        if self.editing.edit_mode:
            if self.state_moving_circle:
                (id_center, id_circle) = self.centers_and_circles[self.index_circle]
                self.do_move_circle(event, id_center, id_circle)
            if self.state_drawing_circle:
                (id_center, id_circle) = self.centers_and_circles[self.index_circle]
                x, y, _, _ = self.CanvasBee.canvas.coords(id_center)
                self.draw_circle2(event, x, y)

    def start_move_circle2(self, event, id_center, id_circle):
        self.CanvasBee.canvas.itemconfig(id_circle, outline="yellow", width=4)
        self.CanvasBee.canvas.itemconfig(id_circle, outline="yellow", width=4)

    def do_move_circle(self, event, id_center, id_circle):
        if self.editing.edit_mode:
            x_center, y_center, _, _ = self.CanvasBee.canvas.coords(id_center)
            self.CanvasBee.canvas.move(id_center, event.x - x_center, event.y - y_center)
            self.CanvasBee.canvas.move(id_circle, event.x - x_center, event.y - y_center)

    # Tengo que poner esto también porque como para dibujar móviles hago un click (y tiene un delay de 300 para poder
    # capturar correctamente el doble click), entonces podría pasar que se activase el evento del release antes de
    # dibujar. En ese caso se sale de rango y salta excepción. Así lo evitamos.
    def mouse_click_release(self, event):
        self.root.after(300, self.ButtonRelease_1_handler, event)

    def ButtonRelease_1_handler(self, event):
        if self.editing.edit_mode:
            if self.state_moving_circle:  # If we were moving a circle
                (id_center, id_circle) = self.centers_and_circles[self.index_circle]
                self.change_color_drawn_circle(event, id_circle)
                self.index_circle = -1
                self.state_moving_circle = False
                self.move_circle_opencv_list(id_center,
                                             id_circle)  # Actualizamos en la lista de círculos de opencv la nueva posición
            if self.state_drawing_circle:  # If we were drawing a circle
                (id_center, id_circle) = self.centers_and_circles[self.index_circle]
                self.change_color_drawn_circle(event, id_circle)
                self.index_circle = -1
                self.state_drawing_circle = False

                self.add_circle_opencv_list(id_center, id_circle)
            # self.getResults()  # To update the text of the results

    def draw_center2(self, event):
        # First we print the center
        x1, y1 = (event.x - 1), (event.y - 1)
        x2, y2 = (event.x + 1), (event.y + 1)
        id_center = self.CanvasBee.canvas.create_oval(x1, y1, x2, y2, width=4, outline="red")
        id_circle = None
        self.centers_and_circles.append((id_center, id_circle))  # Add to the list of centers and circles
        self.index_circle = len(self.centers_and_circles) - 1  # The new index is the last position
        self.draw_circle2(event, x1, y1)

    def draw_circle2(self, event, x, y):
        if self.editing.edit_mode:
            (id_center, id_circle) = self.centers_and_circles[self.index_circle]
            self.CanvasBee.canvas.delete(id_circle)
            Radius = event.x / 10
            id_circle = self.CanvasBee.canvas.create_oval((x - Radius, y - Radius, x + Radius, y + Radius),
                                                          width=2, outline='green')
            self.centers_and_circles[self.index_circle] = (id_center, id_circle)

    def change_color_drawn_circle(self, event, id_circle):
        if self.editing.edit_mode:
            self.CanvasBee.canvas.itemconfig(id_circle, outline="green", width=4)

    def delete_circle(self, event):
        if self.editing.edit_mode:
            self.save_actual_state() #Guardo el estado antes de eliminar, para poder deshacer.
            for (id_center, id_circle) in self.centers_and_circles:
                x, y, _, _ = self.CanvasBee.canvas.coords(id_center)
                if (x <= event.x + 10 and x >= event.x - 10 and y >= event.y - 10 and y <= event.y + 10):
                    print("Deleted circle with center ", (x, y))
                    # Primero actualizo la lista de opencv.
                    self.delete_circle_opencv_list(id_center, id_circle)

                    # Borro
                    self.centers_and_circles.remove((id_center, id_circle))  # Delete the elements from the list
                    self.CanvasBee.canvas.delete(id_center)
                    self.CanvasBee.canvas.delete(id_circle)
                    break  # We only delete one circle

    def export_csv(self):
        f = filedialog.asksaveasfile(mode='w', defaultextension=".csv")
        f.write("FileName;MinRadius;MaxRadius;Param1;Param2;MediumCellSize;Scale;CameraHeigh;DiluentParts;TotalSperms;TotalStatic;TotalMotile;MotilePercentage;Concentration\n")
        l = self.miniatures.list_videos
        for analyzed_video in l:
            total_static = sum(n for (_, n) in analyzed_video.contours)
            total_sperms = total_static + analyzed_video.number_circles
            percentage = analyzed_video.number_circles / total_sperms * 100
            percentage = str("%.2f" % round(percentage, 2))
            total_motile = str(analyzed_video.number_circles)

            height, width = analyzed_video.frames[0].frame.shape  # Cojo los tamaños del primer frame
            volume = analyzed_video.micronsPerPixel * width * analyzed_video.micronsPerPixel * height * analyzed_video.cameraDepth / 1e12
            concentration = (analyzed_video.number_circles + total_static) / (volume * 1e6)
            concentration = round(concentration, 2)
            concentration = concentration * (analyzed_video.diluent + 1)

            f.write(analyzed_video.file_path + ";")

            f.write(str(analyzed_video.minRadius)+";")
            f.write(str(analyzed_video.maxRadius) + ";")
            f.write(str(analyzed_video.param1) + ";")
            f.write(str(analyzed_video.param2) + ";")
            f.write(str(analyzed_video.mediumCellSize) + ";")
            f.write(str(analyzed_video.micronsPerPixel) + ";")
            f.write(str(analyzed_video.cameraDepth) + ";")
            f.write(str(analyzed_video.diluent) + ";")

            f.write(str(total_sperms) + ";")
            f.write(str(total_static) + ";")
            f.write(total_motile + ";")
            f.write(percentage + ";")
            f.write(str(concentration) + "\n")
        f.close()

    def show_blank_canvas(self):
        self.CanvasBee.photo = Image.open(r'icons/blank_image.png')
        self.CanvasBee.photo = self.CanvasBee.photo.resize((960, 600), Image.ANTIALIAS)
        self.CanvasBee.photo = ImageTk.PhotoImage(image=self.CanvasBee.photo)
        self.CanvasBee.canvas.create_image(0, 0, image=self.CanvasBee.photo, anchor=tk.NW)

    def reset(self):
        self.stopVideo()
        self.CanvasBee.canvas.delete("all")  # MUY IMPORTANTE: Si no por debajo se quedarán los vídeos funcionando
        # aunque por encima muestre la imagen en blanco.
        self.root.update()
        self.show_blank_canvas()

        self.options.reset_options()

        self.time_required.set(0)

        self.state_analysing.set("Finished!")

        self.miniatures.stop_video = True

        self.resultsString.set("No results currently")
        self.videoInfoText.set("No video selected")
        self.editing.edit_mode = False

        self.miniatures.deleteMiniatures()
        self.root.update()

    def motion_handler(self, event):
        if self.editing.edit_mode:
            id_contour_to_print = None
            id_number_to_print = None
            for (id_contour, list_id_points, id_number) in self.contours:
                for id_point in list_id_points:
                    x, y, _, _ = self.CanvasBee.canvas.coords(id_point)
                    if (x <= event.x + 10 and x >= event.x - 10 and y >= event.y - 10 and y <= event.y + 10):
                        id_contour_to_print = id_contour
                        id_number_to_print = id_number
                        break
                    self.CanvasBee.canvas.itemconfig(id_contour,
                                                     fill="red")  # Pinto de rojo para que cuando salga fuera esté como estaba.
                self.CanvasBee.canvas.itemconfig(id_number,
                                                 fill="magenta")  # Pinto de magenta el número para que cuando salga fuera esté como estaba.
                if id_contour_to_print is not None:
                    break
            if id_contour_to_print is not None:
                self.CanvasBee.canvas.itemconfig(id_contour_to_print, fill="yellow")
                self.CanvasBee.canvas.itemconfig(id_number_to_print, fill="yellow")

    def Double_Button1_handler(self, event):
        if self.editing.edit_mode:  # and self.double_click_flag:
            if self.state_drawing_contour:  # Si ya habíamos empezado y recibimos el doble click, entonces acabamos y pintamos.
                self.state_drawing_contour = False
                self.draw_contour.append((event.x, event.y))
                flattened = [a for x in self.draw_contour for a in x]
                if len(flattened) > 2:
                    list_id_points = []
                    self.CanvasBee.canvas.delete(self.id_temp_contour)
                    id_contour = self.CanvasBee.canvas.create_line(*flattened, smooth=1, fill="red", width=4)

                    id_number = self.CanvasBee.canvas.create_text(event.x - 50, event.y, text="1", fill="magenta",
                                                                  font=('Helvetica 15 bold'))
                    for (x, y) in self.draw_contour:
                        id_point = self.CanvasBee.canvas.create_line(x, y, x + 1, y, fill='red', width=4,
                                                                     state="hidden")  # Los pongo ocultos
                        list_id_points.append(id_point)
                    self.contours.append((id_contour, list_id_points, id_number))
                    self.add_contour_opencv_list(id_contour, list_id_points, id_number)
            else:  # Si no, empezamos
                self.save_actual_state()  # Guardo el estado antes de hacer nada, para poder deshacer.
                self.state_drawing_contour = True
                self.draw_contour = []
                self.draw_contour.append((event.x, event.y))

    def edit_mode(self):
        self.draw_contour = []
        self.stopVideo()
        self.editing.edit_mode = True
        self.CanvasBee.canvas.delete("all")
        if self.miniatures.current_video_name != "":
            self.miniatures.stop_video = True
            if self.miniatures.cap is not None:
                self.miniatures.cap.release()
            self.CanvasBee.canvas.update()

            v = next(x for x in self.miniatures.list_videos if
                     x.file_path == self.miniatures.current_video_name)  # Pillo el videoAnalyzer correspondiente
            print(v.file_path)
            cap = cv.VideoCapture(v.file_path)
            success, frame = cap.read()  # Read the first frame
            # Print the frame:
            cv2image = cv.cvtColor(frame, cv.COLOR_BGR2RGBA)
            img = Image.fromarray(cv2image)
            img = img.resize((960, 600), Image.ANTIALIAS)
            imgtk = ImageTk.PhotoImage(image=img)
            self.CanvasBee.canvas.create_image(0, 0, image=imgtk, anchor=tk.NW)
            self.CanvasBee.photo = imgtk
            self.CanvasBee.canvas.update()

            self.draw_circles_from_openCV_to_GUI(v.frames[0].circles_opencv)  # Dibujo los círculos del frame 0
            self.draw_contours_from_openCV_to_GUI(v.contours)

    def add_circle_opencv_list(self, id_center, id_circle):
        v = next(x for x in self.miniatures.list_videos if
                 x.file_path == self.miniatures.current_video_name)  # Pillo el videoAnalyzer correspondiente
        x1_center, y1_center, x2_center, y2_center = self.CanvasBee.canvas.coords(id_center)
        x1_circle, y1_circle, x2_circle, y2_circle = self.CanvasBee.canvas.coords(id_circle)
        radio = -1 * (x1_circle - x1_center)
        for frame in v.frames:
            frame.circles_opencv.append((int(x1_center * 2), int(y1_center * 2), int(radio * 2)))
        v.number_circles += 1
        v.getResults()  # Para actualizar el texto de los resultados
        v.update_required = True

    def delete_circle_opencv_list(self, id_center, id_circle):
        v = next(x for x in self.miniatures.list_videos if
                 x.file_path == self.miniatures.current_video_name)  # Pillo el videoAnalyzer correspondiente
        i = self.centers_and_circles.index((id_center, id_circle))

        for frame in v.frames:
            frame.circles_opencv.pop(i)  # Borro el elemento en la posición i de todos
        v.number_circles = v.number_circles - 1
        v.getResults()  # Para actualizar el texto de los resultados
        v.update_required = True  # Aquí marco que hay que actualizar, pero solo lo hará al pulsar el icono

    def add_contour_opencv_list(self, id_contour, list_id_points, id_number):
        v = next(x for x in self.miniatures.list_videos if
                 x.file_path == self.miniatures.current_video_name)  # Pillo el videoAnalyzer correspondiente
        list_points = []
        for id_point in list_id_points:
            x, y, _, _ = self.CanvasBee.canvas.coords(id_point)
            list_points.append([[int(x) * 2, int(y) * 2]])
        n = int(self.CanvasBee.canvas.itemcget(id_number, 'text'))  # Para obtener el numerito que tiene
        l = np.array(list_points, dtype=np.int32)
        v.contours.append((l, n))
        v.getResults()
        v.update_required = True

    def move_circle_opencv_list(self, id_center, id_circle):
        v = next(x for x in self.miniatures.list_videos if
                 x.file_path == self.miniatures.current_video_name)  # Pillo el videoAnalyzer correspondiente
        i = self.centers_and_circles.index((id_center, id_circle))
        x1_center, y1_center, x2_center, y2_center = self.CanvasBee.canvas.coords(id_center)
        for frame in v.frames:
            (_, _, r) = frame.circles_opencv[i]  # Cojo lo que había
            frame.circles_opencv[i] = (int(x1_center * 2), int(y1_center * 2),
                                       r)  # Le pongo el nuevo centro (a todos los frames), manteniendo el r
        v.getResults()  # Para actualizar el texto de los resultados
        v.update_required = True  # Aquí marco que hay que actualizar, pero solo lo hará al pulsar el icono

    def modify_number_contour_opencv_list(self, id_contour, list_id_points, id_number):
        v = next(x for x in self.miniatures.list_videos if
                 x.file_path == self.miniatures.current_video_name)  # Pillo el videoAnalyzer correspondiente
        i = self.contours.index((id_contour, list_id_points,
                                 id_number))  # Pillo el índice en los contornos GUI (coincidirá con el íncide en contornos OpenCV)
        (list_contours, n) = v.contours[i]  # Esto es lo que había
        n = int(self.CanvasBee.canvas.itemcget(id_number, 'text'))  # Para obtener el numerito que tiene ahora
        v.contours[i] = (list_contours, n)  # Pongo el nuevo
        v.getResults()

    def save_actual_state(self):
        v = next(x for x in self.miniatures.list_videos if
                 x.file_path == self.miniatures.current_video_name)  # Pillo el videoAnalyzer correspondiente
        Copy_circles_opencv = copy.deepcopy(v.frames)
        Copy_contours = copy.deepcopy(v.contours)
        self.last_state = (self.miniatures.current_video_name, Copy_circles_opencv, Copy_contours, v.number_circles)

    def undo(self, event):
        if self.editing.edit_mode and self.last_state is not None:
            v = next(x for x in self.miniatures.list_videos if
                     x.file_path == self.miniatures.current_video_name)  # Pillo el videoAnalyzer correspondiente
            (video_name, Copy_circles_opencv, Copy_contours, number_circles) = self.last_state
            if video_name == self.miniatures.current_video_name:
                # Solo hago cosas si estoy en el mismo (si no, si he editado un vídeo y me muevo a otro video
                # diferente y hago CTRL + z, me dibujará los círculos del primer vídeo en el segundo.
                v.frames = Copy_circles_opencv
                v.contours = Copy_contours
                v.number_circles = number_circles
                v.getResults()
                v.update_required = True
                #Borramos lo que había, volvemos a dibujar el primer frame, los círculos y los contornos.
                self.CanvasBee.canvas.delete("all")
                cap = cv.VideoCapture(v.file_path)
                success, frame = cap.read()  # Read the first frame
                # Print the frame:
                cv2image = cv.cvtColor(frame, cv.COLOR_BGR2RGBA)
                img = Image.fromarray(cv2image)
                img = img.resize((960, 600), Image.ANTIALIAS)
                imgtk = ImageTk.PhotoImage(image=img)
                self.CanvasBee.canvas.create_image(0, 0, image=imgtk, anchor=tk.NW)
                self.CanvasBee.photo = imgtk
                self.CanvasBee.canvas.update()

                self.draw_circles_from_openCV_to_GUI(v.frames[0].circles_opencv)  # Dibujo los círculos del frame 0
                self.draw_contours_from_openCV_to_GUI(v.contours)
                self.last_state = None



# if __name__ == "__main__":
#     if sys.platform.startswith('win'):
#         # On Windows calling this function is necessary.
#         multiprocessing.freeze_support()  # Funcionará con onedir pero no con onefile
#     App()

import copy
import numpy as np
import cv2 as cv
import time
import os
from Domain.Utils import *

import matplotlib.pyplot as plt
from Domain.FrameVideo import FrameVideo
from skimage.morphology import skeletonize
from multiprocessing import Pool

class VideoAnalyzer:

    def __init__(self, file_path, resultsString):
        self.file_path = file_path
        #self.detected_circles = []
        #self.contours = []
        i = self.file_path.rindex("/")
        self.outputVideo = file_path[:i] + "/Output/" + file_path[i + 1:]
        os.makedirs(file_path[:i] + "/Output/", exist_ok=True)
        self.frames = []
        self.contours = []
        self.number_circles = 0
        self.resultsString = resultsString
        self.update_required = False

        # Default values (not as StringVar, IntVar, etc).
        self.minRadius = 25
        self.maxRadius = 45
        self.param1 = 80
        self.param2 = 35
        self.mediumCellSize = 180
        self.micronsPerPixel = 0.59 #Default value
        self.cameraDepth = 10
        self.diluent = 0
        #self.concentration = 0.0


    def getResults(self):
        number_contours = sum(n for (_, n) in self.contours)
        total_sperms = number_contours + self.number_circles
        percentage = (self.number_circles) / total_sperms * 100
        height, width = self.frames[0].frame.shape # Cojo los tamaños del primer frame
        volume = self.micronsPerPixel * width * self.micronsPerPixel * height * self.cameraDepth / 1e12
        concentration = (self.number_circles + number_contours) / (volume * 1e6)
        concentration = concentration * (self.diluent + 1) # El diluyente.
        concentration = round(concentration, 2) #Lo dejo redondeado a dos decimales
        textResult = "Total number of sperms: " + str(total_sperms) + "\n" \
                      "Total static: " + str(number_contours) + "\n" \
                      "Total motile: " + str(self.number_circles) + "\n" \
                      "Motile percentage: " + str("%.2f" % round(percentage, 2)) + "%\n" \
                      "Concentration: " + str(concentration)
        self.resultsString.set(textResult)


    def videoSpermDetection(self, options):
        inicial = time.time()
        self.frames = [] #Reiniciamos por si acaso
        self.contours = []
        video = self.file_path
        outputVideo = self.outputVideo

        filterKernel = Utils.filterKernel()
        morphKernel = Utils.morphKernel()
        horizontalLinesKernel = Utils.horizontalLinesKernel()
        verticalLinesKernel = Utils.verticalLinesKernel()
        kernel45Lines = Utils.kernel45Lines()
        kernel_45Lines = Utils.kernel_45Lines()

        th = 70
        (minRadius, maxRadius, param1, param2, mediumCellSize, micronsPerPixel, cameraDepth, diluent) = options
        #micronsPerPixel = 1
        self.minRadius = minRadius
        self.maxRadius = maxRadius
        self.param1 = param1
        self.param2 = param2
        self.mediumCellSize = mediumCellSize
        self.micronsPerPixel = micronsPerPixel
        self.cameraDepth = cameraDepth
        self.diluent = diluent
        # mediumCellSize estaba en micras, pasamos a pixeles y ya trabajamos en pixeles a partir de ahora
        mediumCellSize = mediumCellSize / micronsPerPixel
        minimumCellSize = mediumCellSize * 0.20  # ponerlo como parámetro ?
        minArea = minimumCellSize * 4 #/ micronsPerPixel

        vidcap = cv.VideoCapture(video)
        success, image = vidcap.read()

        circleList = []
        cimgList = []

        if success:
            height, width, depth = image.shape
            iimg = np.full((height, width), 255, np.uint8)
            w = width + 50
            h = height + 50
        i = 0

        while success:
            f = FrameVideo(image, i)
            i += 1
            self.frames.append(f)
            cimgList.append(image)
            success, image = vidcap.read()

        vidcap.release()

        jobs = [(frame, options) for frame in self.frames] #Tengo que hacer esto para poder pasar multiples argumentos
        with Pool() as p:
            self.frames = p.map(FrameVideo.analyzeFrame, jobs)
            p.close()

        final = time.time() - inicial
        print("Time to compute circles (Hough transform)", final)

        for frame in self.frames:
            circleList.append(frame.circles_opencv)
            threshold, img_umb = cv.threshold(frame.frame, th, 255, cv.THRESH_BINARY)
            img_umb = cv.dilate(img_umb, morphKernel)
            img_umb = cv.dilate(img_umb, morphKernel)
            img_umb = cv.dilate(img_umb, morphKernel)
            iimg = cv.bitwise_and(iimg, img_umb)

        # I compute the static sperms
        img = cv.erode(iimg, morphKernel)

        contours, hierarchy = cv.findContours(img, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        contours1 = []

        for c in contours:
            area = cv.contourArea(c)
            minRectBox = cv.minAreaRect(c)
            minRectArea = cv.contourArea(cv.boxPoints(minRectBox))
            if (area < minArea) or ((area / minRectArea) > 0.3): # or minRectArea < boundingBoxMinArea:  #
                contours1.append(c)

        cimg_umb = cv.cvtColor(img, cv.COLOR_GRAY2BGR)
        cv.drawContours(cimg_umb, contours1, -1, (0, 0, 0), thickness=cv.FILLED)
        img_umb = cv.cvtColor(cimg_umb, cv.COLOR_BGR2GRAY)
        # imageShow(img_umb)

        circles = cv.HoughCircles(img_umb, cv.HOUGH_GRADIENT, 1, 25, param1=50, param2=20, minRadius=10,
                                  maxRadius=maxRadius)
        if circles is not None:
            circles = np.uint16(np.around(circles))

            for (x, y, r) in circles[0, :]:
                # We draw circles in black, with radius 13:
                cv.circle(img_umb, (x, y), r - 3, 0, 13)

            # I compute contours again

            contours, hierarchy = cv.findContours(img_umb, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

            # I choose those that correspond to thin lines
            contours2 = []
            for c in contours:
                area = cv.contourArea(c)
                minRectBox = cv.minAreaRect(c)
                minRectArea = cv.contourArea(cv.boxPoints(minRectBox))
                if (area > minArea) and ((area / minRectArea) < 0.3): # and minRectArea > boundingBoxMinArea:  # and (convexHullArea > 3000)
                    contours2.append(c)

            # For each contour corresponding to a thin line, I compute the contour extrems,
            # I determine a 20x20 square over the image and I look for horizontal, vertical, 45 or -45 lines
            # Depending on the type of lines found in the square, I determine a rectangle for each extrem where I look
            # for white pixels. For each white pixel found I add a line between this pixel and the corresponding extrem

            lines = []

            for c in contours2:

                extLeft = tuple(c[c[:, :, 0].argmin()][0])
                extRight = tuple(c[c[:, :, 0].argmax()][0])
                extTop = tuple(c[c[:, :, 1].argmin()][0])
                extBot = tuple(c[c[:, :, 1].argmax()][0])
                ext = [extLeft, extRight, extTop, extBot]
                xLeft = extLeft[0]
                yLeft = extLeft[1]
                xRight = extRight[0]
                yRight = extRight[1]
                xTop = extTop[0]
                yTop = extTop[1]
                xBot = extBot[0]
                yBot = extBot[1]

                # I determine the coordinages of the four rectangles where I will look for white pixels
                rectangles = [[xLeft - 30, xLeft, yLeft, yLeft], [xRight, xRight + 30, yRight, yRight],
                              [xTop, xTop, yTop - 30, yTop], [xBot, xBot, yBot, yBot + 30]]
                i = 0
                for y, x in ext:
                    # I discard extrems which are closed to the borders
                    if ((x >= 50) and x <= h and (y >= 50) and y <= w):

                        square = img_umb[x - 10:x + 11, y - 10:y + 11]

                        coh = Utils.convolve(square, horizontalLinesKernel)
                        cov = Utils.convolve(square, verticalLinesKernel)
                        co45 = Utils.convolve(square, kernel45Lines)
                        co_45 = Utils.convolve(square, kernel_45Lines)
                        if ((coh > 700).sum() > 2):
                            if (i == 0):
                                rectangles[i][2] = yLeft - 15
                                rectangles[i][3] = yLeft + 15
                            elif (i == 1):
                                rectangles[i][2] = yRight - 15
                                rectangles[i][3] = yRight + 15
                        if ((cov > 700).sum() > 2):
                            if (i == 2):
                                rectangles[i][0] = xTop - 15
                                rectangles[i][1] = xTop + 15
                            elif (i == 3):
                                rectangles[i][0] = xBot - 15
                                rectangles[i][1] = xBot + 15
                        if ((co45 > 700).sum() > 2):
                            if (i == 0):
                                rectangles[i][3] = yLeft + 30
                            elif (i == 1):
                                rectangles[i][2] = yRight - 30
                            elif (i == 2):
                                rectangles[i][1] = xTop + 30
                            elif (i == 3):
                                rectangles[i][0] = xBot - 30
                        if ((co_45 > 700).sum() > 2):

                            if (i == 0):
                                rectangles[i][2] = yLeft - 30
                            elif (i == 1):
                                rectangles[i][3] = yRight + 30
                            elif (i == 2):
                                rectangles[i][0] = xTop - 30
                            elif (i == 3):
                                rectangles[i][1] = xBot + 30
                    i = i + 1

                # It is possible to do this in one instruction?
                rectangles_im = [img_umb[rectangles[0][2]:rectangles[0][3], rectangles[0][0]:rectangles[0][1]],
                                 img_umb[rectangles[1][2]:rectangles[1][3], rectangles[1][0]:rectangles[1][1]],
                                 img_umb[rectangles[2][2]:rectangles[2][3], rectangles[2][0]:rectangles[2][1]],
                                 img_umb[rectangles[3][2]:rectangles[3][3], rectangles[3][0]:rectangles[3][1]]]

                for k in range(4):
                    rectanglek = rectangles[k]
                    rectangles_imk = rectangles_im[k]
                    extk = ext[k]

                    for i in range(rectangles_imk.shape[0]):
                        for j in range(rectangles_imk.shape[1]):
                            if (rectangles_imk[i, j] == 255):
                                l = [[extk[0], extk[1]], [rectanglek[0] + j, rectanglek[2] + i]]
                                lines.append(l)

            # I draw the lines and compute contours again
            line_thickness = 3
            for l in lines:
                cv.line(img_umb, (l[0][0], l[0][1]), (l[1][0], l[1][1]), 255, thickness=line_thickness)

        contours, hierarchy = cv.findContours(img_umb, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

        # I choose those corresponding to thin lines
        contours2 = []

        for c in contours:
            area = cv.contourArea(c)
            #minRectBox = cv.minAreaRect(c) #ESTO ES DISTINTO EN LA DE ANA
            minRectBox = cv.boxPoints(cv.minAreaRect(c))
            ax1 = np.sqrt(np.sum(np.square(minRectBox[0] - minRectBox[1])))
            ax2 = np.sqrt(np.sum(np.square(minRectBox[1] - minRectBox[2])))
            minRectArea = cv.contourArea(minRectBox)
            #minRectArea = cv.contourArea(cv.boxPoints(minRectBox)) #ESTO ES LO QUE HABÍA
            if ((ax1 > maxRadius * 2 + 10) or (ax2 > maxRadius * 2 + 10)) \
                    and (area > minArea) and ((area / minRectArea) < 0.3):  # and minRectArea > boundingBoxMinArea: # and (convexHullArea > 3000)
                contours2.append(c)


        # I compute the indices of the circles in each frame

        indices = []
        circles0 = circleList[0]
        for k in range(0, len(circles0)):
            indices.append([k])

        i = 0
        for (x1, y1, r1) in circles0:

            for m in range(1, len(cimgList)):
                circles1 = circleList[m - 1]
                circles2 = circleList[m]

                jointCircles = []

                p1 = np.array([x1, y1], dtype=np.long)
                j = 0
                for (x2, y2, r2) in circles2:

                    p2 = np.array([x2, y2], dtype=np.long)

                    if (np.sqrt(np.sum(np.square(p1 - p2))) <= r1):
                        jointCircles.append(j)
                    j = j + 1
                if len(jointCircles) == 1:
                    indices[i].append(jointCircles[0])
                    circle = circles2[jointCircles[0]]
                    x1 = circle[0]
                    y1 = circle[1]
                    r1 = circle[2]
                elif len(jointCircles) >= 2:
                    circle0 = circles2[jointCircles[0]]
                    p2 = np.array([circle0[0], circle0[1]], dtype=np.long)
                    dmin = np.sqrt(np.sum(np.square(p1 - p2)))
                    imin = 0
                    for k in range(1, len(jointCircles)):
                        circle20 = circles2[jointCircles[k]]

                        p2 = np.array([circle20[0], circle20[1]], dtype=np.long)
                        if np.sqrt(np.sum(np.square(p1 - p2))) < dmin:
                            dmin = np.sqrt(np.sum(np.square(p1 - p2)))
                            imin = k
                    indices[i].append(jointCircles[imin])
                    circle = circles2[jointCircles[imin]]
                    x1 = circle[0]
                    y1 = circle[1]
                    r1 = circle[2]


                else:
                    indices[i].append(-1)

            i = i + 1

        # In each colored image, I draw the circles

        cmap = plt.get_cmap('tab20c')

        good_indices = []
        final_indices = []

        i = 0
        for l in indices:
            if l.count(-1) < (len(l) / 2):  # I consider those that appear at least in half of the frames
                j = len(l) - 1
                while l[j] == -1:
                    j = j - 1
                final_indices.append([j, l[j]])
            else:
                final_indices.append([-1, -1])
            i = i + 1

        # print(final_indices)

        i = 0
        for l in indices:
            if (final_indices[i][0] != -1) and (l.count(-1) < (len(l) / 2)):
                j = final_indices[i][0]
                k = final_indices[i][1]

                rep = []
                for s in range(i + 1, len(indices)):
                    if (final_indices[s][0] == j and final_indices[s][1] == k):
                        rep.append(s)

                if len(rep) > 0:
                    max = l.count(-1)
                    for s in rep:
                        l2 = indices[s].count(-1)
                        if l2 > m:
                            m = l2
                            i = s

                    for s in rep:
                        final_indices[s][0] = -1

                good_indices.append(indices[i])

            i = i + 1

        self.number_circles = len(good_indices)


        # print("Number of motile sperms: ", number_circles)

        i = 1
        final_circles = []
        for k in range(0,len(good_indices[0])):
            final_circles.append([])
        for l in good_indices:
            colorVal = cmap(i%20)

            for k in range(0,len(cimgList)):
                cimagek = cimgList[k]
                circlesk = circleList[k]
                indice = l[k]

                if (indice != -1):
                    circle = circlesk[indice]

                    x = circle[0]
                    y = circle[1]
                    r = circle[2]

                final_circles[k].append(circle)
                cv.circle(cimagek,(x,y),r+10,(colorVal[0]*255,colorVal[1]*255,colorVal[2]*255),2)
                        # draw the center of the circle
                cv.circle(cimagek,(x,y),2,(255,0,255),3)

                cimagek = cv.putText(cimagek, str(i), (int(x)-10,int(y)+10), cv.FONT_HERSHEY_SIMPLEX, 1, (colorVal[0]*255,colorVal[1]*255,colorVal[2]*255), 2, cv.LINE_AA)
            i = i+1

        #Con esto ponemos las listas de círculos buenas (de lo que realmente se pinta).
        for frame, circles in zip(self.frames, final_circles):
            frame.circles_opencv = circles


        # In each colored image, I draw the contours corresponding to the static sperms

        #     img_umb = cv.imread("aux_img.jpg",0)
        #     img_umb = cv.dilate(img_umb,morphKernel)
        #     contours3, hierarchy = cv.findContours(img_umb, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        k = 0
        for c in contours2:
            img_umb = np.zeros((img.shape[0], img.shape[1]), dtype=np.uint8)
            cimg_umb = cv.cvtColor(img_umb, cv.COLOR_GRAY2BGR)
            contours1 = []
            contours1.append(c)
            cv.drawContours(cimg_umb, contours1, -1, (255, 255, 255), thickness=cv.FILLED)
            img_umb = cv.cvtColor(cimg_umb, cv.COLOR_BGR2GRAY)
            img_umb[img_umb > 0] = 1

            skeleton = skeletonize(img_umb).astype(int)
            l = np.sum(skeleton > 0)
            #         print("Longitud del contorno: ",l)
            #if (80 < l and l < 500):
            if (0.2 * mediumCellSize < l and l < 1.5 * mediumCellSize):
                k = k + 1
                self.contours.append((c, 1))
            #elif l >= 500:
            elif l >= 1.5 * mediumCellSize:
                k = k + int((l + 150) / 300)
                self.contours.append((c, int(round(l/mediumCellSize))))


        #print("CONTORNOS", self.contours)


        # In each colored image, I draw the contours corresponding to the static sperms

        for cimg in cimgList:
            cv.drawContours(cimg, contours2, -1, (0, 0, 255), thickness=2)

        # Finally I construct the output video with all the images
        size = (width, height)
        out = cv.VideoWriter(outputVideo, cv.VideoWriter_fourcc(*'DIVX'), 15, size)
        for cimg, frame in zip(cimgList, self.frames):
            frame.output_frame = cimg

        for frame in self.frames:
            out.write(frame.output_frame)
        out.release()

        #We update the concentration:
        #volume = micronsPerPixel * width * micronsPerPixel * height * cameraDepth / 1e12
        #number_contours = sum(n for (_, n) in self.contours)
        #self.concentration = (self.number_circles + number_contours) / (volume * 1e6)
        #self.concentration = round(self.concentration, 2) #Lo dejo redondeado a dos decimales

        final = time.time() - inicial
        print("Final time: ", final)
        #self.contours = contours2



    def updateVideo(self):
        height, width = self.frames[0].frame.shape # Cojo los tamaños del primer frame
        size = (width, height)
        #print(self.frames[0].output_frame.shape) #Creo que aquí esta el problema, esto devuelve 3 cosas, no 2.
        out = cv.VideoWriter(self.outputVideo, cv.VideoWriter_fourcc(*'DIVX'), 15, size)
        contours_to_draw = [a[0] for a in self.contours]
        cmap = plt.get_cmap('tab20c')
        for frame in self.frames:
            #Pinto los contornos
            #cv.drawContours(frame.frame, self.contours, -1, (0, 0, 255), thickness=2)
            r = cv.cvtColor(frame.frame, cv.COLOR_GRAY2BGR)
            frame.output_frame = cv.polylines(r, contours_to_draw, isClosed = False, color = (0, 0, 255), thickness=2)

            #Ahora pinto los círculos
            i = 1
            for (x, y, r) in frame.circles_opencv:
                colorVal = cmap(i % 20)
                frame.output_frame = cv.circle(frame.output_frame, (x, y), r + 10,
                                               (colorVal[0] * 255, colorVal[1] * 255, colorVal[2] * 255), 2)
                # draw the center of the circle
                frame.output_frame = cv.circle(frame.output_frame, (x, y), 2, (255, 0, 255), 3)
                # draw the number of the circle
                frame.output_frame = cv.putText(frame.output_frame, str(i), (int(x) - 10, int(y) + 10), cv.FONT_HERSHEY_SIMPLEX, 1,
                                     (colorVal[0] * 255, colorVal[1] * 255, colorVal[2] * 255), 2, cv.LINE_AA)
                i += 1
            out.write(frame.output_frame)



        out.release()
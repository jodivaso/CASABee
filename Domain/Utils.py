import numpy as np
import cv2 as cv
from PIL import ImageTk, Image, ImageDraw

class Utils:


    #He dudado si hacerlo así con métodos estáticos o es mejor variables globales.

    @staticmethod
    def filterKernel():
        return np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])

    @staticmethod
    def morphKernel():
        return np.ones((3, 3), np.uint8)

    @staticmethod
    def horizontalLinesKernel():
        return np.array([[-1, -1, -1], [2, 2, 2], [-1, -1, -1]])

    @staticmethod
    def verticalLinesKernel():
        return np.array([[-1, 2, -1], [-1, 2, -1], [-1, 2, -1]])

    @staticmethod
    def kernel45Lines():
        return np.array([[-1, -1, 2], [-1, 2, -1], [2, -1, -1]])

    @staticmethod
    def kernel_45Lines():
        return np.array([[2, -1, -1], [-1, 2, -1], [-1, -1, 2]])

    @staticmethod
    def convolve(image, kernel):
        # https://www.pyimagesearch.com/2016/07/25/convolutions-with-opencv-and-python/
        # grab the spatial dimensions of the image, along with
        # the spatial dimensions of the kernel
        (iH, iW) = image.shape[:2]
        (kH, kW) = kernel.shape[:2]
         # allocate memory for the output image, taking care to
            # "pad" the borders of the input image so the spatial
            # size (i.e., width and height) are not reduced
        pad = (kW - 1) // 2
        image = cv.copyMakeBorder(image, pad, pad, pad, pad,cv.BORDER_REPLICATE)
        output = np.zeros((iH, iW), dtype="float32")
        # loop over the input image, "sliding" the kernel across
            # each (x, y)-coordinate from left-to-right and top to
            # bottom
        for y in np.arange(pad, iH + pad):
            for x in np.arange(pad, iW + pad):
            # extract the ROI of the image by extracting the
            # *center* region of the current (x, y)-coordinates
            # dimensions
                roi = image[y - pad:y + pad + 1, x - pad:x + pad + 1]
                # perform the actual convolution by taking the
                # element-wise multiplicate between the ROI and
                # the kernel, then summing the matrix
                k = (roi * kernel).sum()
                # store the convolved value in the output (x,y)-
                # coordinate of the output image
                output[y - pad, x - pad] = k
        return output

    @staticmethod
    def img_frame_miniature_with_text(video_name, index, fontColor): #Nombre del vídeo, índice (para poner Video 1, Video 2, etc) y color.
        cap = cv.VideoCapture(video_name)
        cap.set(2, 0)
        ret, frame = cap.read()

        font = cv.FONT_HERSHEY_TRIPLEX
        fontScale = 10
        #fontColor = (255, 255, 255)

        # get coords based on boundary
        # textX = (frame.shape[1] - fontScale*30)
        textX = (fontScale * 30)
        textY = (frame.shape[0] - fontScale * 10)
        bottomLeftCornerOfText = (textX, textY)

        cv.putText(frame, "Video " + str(index),
                   bottomLeftCornerOfText,
                   cv.FONT_HERSHEY_TRIPLEX,
                   fontScale,
                   fontColor,
                   thickness=10)

        im = Image.fromarray(frame)

        im = im.resize((72 * 2, 72), Image.ANTIALIAS)
        img = ImageTk.PhotoImage(image=im)
        cap.release()
        return img

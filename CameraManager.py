import cv2
from matplotlib import pyplot as plt
import numpy as np
import imutils
import easyocr

class CameraManager:
    def __init__(self, ocrLanguages) -> None:
        self.ocrLanguages = ocrLanguages # https://www.jaided.ai/easyocr/
    
    def takePhoto(self):
        cameraPort = 0
        camera = cv2.VideoCapture(cameraPort)
        result, image = camera.read()
        if result:
            return image
        else:
            print("No image detected")
            return None

    def getVehiclePlateNumber(self, imageBGR):
        imageGray = cv2.cvtColor(imageBGR, cv2.COLOR_BGR2GRAY)
        imageGrayFiltered = self.filterNoises(imageGray)
        plateMask = self.findPlateMask(imageGrayFiltered)
        if plateMask is None:
            print("failed to read plate number")
            return None
        plateImage = self.cropPlate(imageGray, plateMask)
        plateNumber = self.readPlateNumber(plateImage)
        return plateNumber

    
    def filterNoises(self, image):
        diameter = 11 # diameter of each pixel neighborhood
        sigmaColor = 17 # value of sigma in the color space. The greater the value, the colors farther to each other will start to get mixed.
        sigmaSpace = 17 # value of sigma in the coordinate space. he greater its value, the more further pixels will mix together, given that their colors lie within the sigmaColor range.
        return cv2.bilateralFilter(image, diameter, sigmaColor, sigmaSpace)
    
    def performCannyEdgeDetection(self, image):
        thresholdLower = 30 # lower threshold value in Hysteresis Thresholding
        thresholdUpper = 200 # upper threshold value in Hysteresis Thresholding
        return cv2.Canny(image, thresholdLower, thresholdUpper)
    
    def _findContours(self, imageEdges):
        keyPoints = cv2.findContours(imageEdges.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(keyPoints)
        return sorted(contours, key=cv2.contourArea, reverse=True)[:10]
    
    def _findPlateCorners(self, contours):
        for contour in contours:
            approx = cv2.approxPolyDP(contour, 10, True)
            if len(approx) == 4:
                return approx
        return None
    
    def findPlateMask(self, image):
        imageEdges = self.performCannyEdgeDetection(image)
        imageContours = self._findContours(imageEdges)
        plateCornersCoordinates = self._findPlateCorners(imageContours)
        if plateCornersCoordinates is None:
            return None
        mask = np.zeros(image.shape, np.uint8)
        cv2.drawContours(mask, [plateCornersCoordinates], 0, 255, -1)
        return mask
    
    def cropPlate(self, image, mask):
        x, y = np.where(mask==255)
        x1, y1 = (np.min(x), np.min(y))
        x2, y2 = (np.max(x), np.max(y))
        return image[x1 : x2+1, y1 : y2+1]
    
    def readPlateNumber(self, plateImage):
        ocrReader = easyocr.Reader(self.ocrLanguages)
        ocrResult = ocrReader.readtext(plateImage)
        return ocrResult[0][-2]

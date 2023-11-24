import unittest
from CameraManager import CameraManager
import cv2

class TestStringMethods(unittest.TestCase):

    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')

    def testPlateNumberRecognition(self):
        cameraManager = CameraManager(['pl', 'en'])
        expectedPlateNumbers = ['PO 156VN', 'HR.26 BR 9044', 'WY 8686W', 'WY 726XE']
        for i in range(4):
            image = cv2.imread(f'testData/vehicle{i}.jpg')
            plateNumber = cameraManager.getVehiclePlateNumber(image)
            self.assertEqual(plateNumber, expectedPlateNumbers[i])

if __name__ == '__main__':
    unittest.main()

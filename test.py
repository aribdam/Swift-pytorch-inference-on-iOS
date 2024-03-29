from scipy import ndimage
import matplotlib.pyplot as plt

def assert_lines(lines):
    
    ''' 
        params [lines] - lines returned from cv2.HoughLinesP()
        
        return value [truth statement] - checking if lines are horizontal or not
                                            we need to avoid horizontal lines
    '''
    
    for x1, y1, x2, y2 in lines[0]:
        return (x2-x1 == 0 or y2-y1 == 0)


def detectPlates(image):
		minPlateW = 50
		minPlateH = 15

		# initialize the rectangular and square kernels to be applied to the image,
		# then initialize the list of license plate regions
		rectKernel = cv2.getStructuringElement(cv2.MORPH_RECT, (13, 5))
		squareKernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

		regions = []

		# convert the image to grayscale, and apply the blackhat operation
		gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
		blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, rectKernel)

		# find regions in the image that are light
		light = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, squareKernel)
		light = cv2.threshold(light, 50, 255, cv2.THRESH_BINARY)[1]

		# compute the Scharr gradient representation of the blackhat image and scale the
		# resulting image into the range [0, 255]
		gradX = cv2.Sobel(blackhat,
			ddepth = cv2.CV_32F,
			dx = 1, dy = 0, ksize = -1)
		gradX = np.absolute(gradX)
		(minVal, maxVal) = (np.min(gradX), np.max(gradX))
		gradX = (255 * ((gradX - minVal) / (maxVal - minVal))).astype("uint8")

		# blur the gradient representation, apply a closing operating, and threshold the
		# image using Otsu's method
		gradX = cv2.GaussianBlur(gradX, (5, 5), 0)
		gradX = cv2.morphologyEx(gradX, cv2.MORPH_CLOSE, rectKernel)
		thresh = cv2.threshold(gradX, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

		# perform a series of erosions and dilations on the image
		thresh = cv2.erode(thresh, None, iterations = 2)
		thresh = cv2.dilate(thresh, None, iterations = 2)

		# take the bitwise 'and' between the 'light' regions of the image, then perform
		# another series of erosions and dilations
		thresh = cv2.bitwise_and(thresh, thresh, mask = light)
		thresh = cv2.dilate(thresh, None, iterations = 2)
		thresh = cv2.erode(thresh, None, iterations = 1)

        # cv2.imwrite("kk2.jpg", thresh)

		# find contours in the thresholded image
		cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

		# loop over the contours
		for c in cnts:
			# grab the bounding box associated with the contour and compute the area and
			# aspect ratio
			(w, h) = cv2.boundingRect(c)[2:]
			aspectRatio = w / float(h)

			# calculate extent for additional filtering
			shapeArea = cv2.contourArea(c)
			boundingboxArea = w * h
			extent = shapeArea / float(boundingboxArea)
			extent = int(extent * 100) / 100

			# compute the rotated bounding box of the region
			rect = cv2.minAreaRect(c)
			box = cv2.boxPoints(rect)

			# ensure the aspect ratio, width, and height of the bounding box fall within
			# tolerable limits, then update the list of license plate regions
			if (aspectRatio > 3 and aspectRatio < 6) and h > minPlateH and w > minPlateW and extent > 0.50:
				print("box", box)
				regions.append(box)

		# return the list of license plate regions
		return regions

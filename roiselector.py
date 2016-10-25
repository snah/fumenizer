import cv2

class CancelException(Exception):
    """Exception indicating the user canceled the operation."""
    pass


class Region:
    """Defines a region of an image given two points."""
    def __init__(self, point1, point2):
        """Create a region from two coordinate tuples."""
        self.point1 = point1
        self.point2 = point2


    def crop(self, image):
        """Rop the image to this region."""
        x_min = min(self.point1[0], self.point2[0])
        x_max = max(self.point1[0], self.point2[0])
        y_min = min(self.point1[1], self.point2[1])
        y_max = max(self.point1[1], self.point2[1])
        return image[y_min:y_max, x_min:x_max]


class ROISelector:
    """Lets the user select a region of interest on an image."""
    def __init__(self, image):
        self.drawing = False
        self.region = Region((0, 0), (0, 0))
        self.image = image


    def run(self):
        """Show the image and let the user draw a rectangle on it.
        
        The user can draw a rectangle by left clicking and dragging
        across the image. Pressing enter accepts the rectangle,
        pressing escape or 'q' raises a CancelException.

        Returns a tuple of two points indicating the ROI.
        """
        cv2.namedWindow('rectangle_window')
        cv2.setMouseCallback('rectangle_window', self._mouse_callback)
        while True:
            cv2.imshow('rectangle_window', self._make_image_with_region_overlay())
            key = cv2.waitKey(20) & 0xff
            if key == 10:
                break
            elif key == 27 or key == ord('q'):
                raise CancelException()
        cv2.destroyWindow('rectangle_window')
        return self.region


    def _mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.region.point1 = x, y
            self.region.point2 = x, y
        elif event == cv2.EVENT_MOUSEMOVE and self.drawing:
            self.region.point2 = x, y
        elif event == cv2.EVENT_LBUTTONUP and self.drawing:
            self.drawing = False
            self.region.point2 = x, y


    def _make_image_with_region_overlay(self):
        temp_image = self.image.copy()
        cv2.rectangle(temp_image, self.region.point1, self.region.point2, (0, 255, 0))
        return temp_image

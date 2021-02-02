from io import BytesIO
from PySide2.QtGui import QImage, QPixmap

import os
from PIL import Image
from pathlib import Path
import numpy as np
from threading import RLock


class Tif:
    def __init__(self, tiffFileName):
        self.tiffFileName = Path(tiffFileName)
        self.__tiff = Image.open(self.tiffFileName)
        self.__redFileName = "redTmp.tif"

        self.channels = self.get_channels()
        self.Z = self.get_z()
        self.T = self.get_t()

        # relative shift
        self.__list_shift = [(0, 0) for i in range(self.T)]
        self.imageNumber = self.channels * self.T * self.Z
        self.currentT = 0
        self.currentZ = 0
        self.currentChannel = 0

        self.shift_range = 8

        self.width = self.__tiff.getbbox()[2]
        self.height = self.__tiff.getbbox()[3]
        self.zoom = 1
        self.__background = Image.new(self.__tiff.mode, (self.width, self.height))

        self._is_running = False
        self._access = RLock()

    def set_shift_range(self, value):
        self.shift_range = value

    def index_from_tzc(self, t=0, z=0, c=0):
        index = t * self.Z * self.channels + z * self.channels + c
        return index

    def get_current_shift(self):
        return self.__list_shift[self.currentT]

    def delta_shift(self, delta, t=None):
        if t is None:
            t = self.currentT

        self.__list_shift[t] = (
            self.__list_shift[t][0] + delta[0],
            self.__list_shift[t][1] + delta[1],
        )

    def tzc_image(self, t=0, z=0, c=0):
        self.__tiff.seek(self.index_from_tzc(t=t, z=z, c=c))

    def set_index(self, t=None, z=None, c=None):
        if t is not None:
            self.currentT = t
        if z is not None:
            self.currentZ = z
        if c is not None:
            self.currentChannel = c

    def get_imagej_metadata(self):
        ls = [v for v in self.__tiff.tag.values()]
        for element in ls:
            if type(element) is not tuple:
                continue
            if len(element) == 0:
                continue
            if type(element[0]) is not str:
                continue
            if "ImageJ" in element[0]:
                return element[0]

        raise RuntimeError(
            "Could not find size of the stack."
            "Are you sure the tiff file is coming from ImageJ ?"
        )

    def format_imagej_metadata(self):
        metadata = self.get_imagej_metadata()
        ret = {
            name: value
            for (name, value) in [
                tuple(x.split("=")) for x in metadata.split("\n") if "=" in x
            ]
        }
        return ret

    def get_t(self):
        dict_metadata = self.format_imagej_metadata()
        return int(dict_metadata["frames"])

    def get_z(self):
        dict_metadata = self.format_imagej_metadata()
        try:
            return int(dict_metadata["slices"])
        except KeyError:
            return 1

    def get_channels(self):
        dict_metadata = self.format_imagej_metadata()
        try:
            return int(dict_metadata["channels"])
        except KeyError:
            return 1

    def run_from_here(self):
        if self._is_running:
            return

        self._is_running = True

        t = self.currentT
        z = self.currentZ
        c = self.currentChannel
        max_t = self.T - 1

        for i in range(t, max_t):
            delta = self.get_best_delta(i, z, c)
            # careful, we shift the next one, not the current one
            self.__list_shift[i + 1] = (
                delta[1],
                delta[0],
            )

        self._is_running = False

    def get_image(self, t, z, c):
        self.tzc_image(c=c, t=t, z=z)
        return self.__tiff.copy()

    def shift(self, img, dx, dy):
        size = img.size if type(img.size) != int else img.shape
        rec = np.zeros(size)
        slx_rec = slice(max(0, dx), min(size[0], size[0] + dx))
        sly_rec = slice(max(0, dy), min(size[1], size[1] + dy))
        slx_sen = slice(max(0, -dx), min(size[0], size[0] - dx))
        sly_sen = slice(max(0, -dy), min(size[1], size[1] - dy))
        rec[slx_rec, sly_rec] = img[slx_sen, sly_sen]
        return rec

    def get_best_delta(self, t, z, c, r=8):
        """
        This function can be optimized by earlystopping, or random exploration and
        lowering of step (start with 3, then 2, then 1)
        """
        r = self.shift_range
        first = np.asarray(self.get_image(t, z, c))
        first = first / np.linalg.norm(first)

        # self.currentT += 1  # WHY ??
        sec = np.asarray(self.get_image(t + 1, z, c))
        sec = sec / np.linalg.norm(sec)

        minimum = 1e9
        coord_min = (0, 0)

        for i in range(-r, r):
            for j in range(-r, r):
                target = self.shift(sec, i, j)
                xd = target - first
                score = np.sum((xd) ** 2)

                if score < minimum:
                    minimum = score
                    coord_min = (i, j)

        return coord_min

    def get_image_file(self):
        with self._access:
            image = self.adjust()
            if self.zoom != 1:
                width = int(self.width * self.zoom)
                height = int(self.height * self.zoom)
                image = image.resize((width, height))

            with BytesIO() as f:
                image.save(f, format="png")
                f.seek(0)
                image_data = f.read()
                qimg = QImage.fromData(image_data)
                patch_qt = QPixmap.fromImage(qimg)
                return patch_qt

    def get_absolute_shift(self, t):
        abs_x, abs_y = 0, 0

        for i in range(t + 1):
            abs_x += self.__list_shift[i][0]
            abs_y += self.__list_shift[i][1]

        return abs_x, abs_y

    def adjust(self):
        self.tzc_image(c=self.currentChannel, t=self.currentT, z=self.currentZ)
        # x    = self.Xs[tIndex][zIndex]
        # y    = self.Ys[tIndex][zIndex]
        t = self.currentT

        # get the right shift
        x, y = self.get_absolute_shift(t)

        x1, y1, x2, y2, xOrigin, yOrigin = 0, 0, self.width, self.height, 0, 0
        if x < 0:
            x1 = abs(x)
            x2 = self.width
            xOrigin = 0
        elif x > 0:
            x1 = 0
            x2 = self.width - x
            xOrigin = x
        if y < 0:
            y1 = abs(y)
            y2 = self.height
            yOrigin = 0
        elif y > 0:
            y1 = 0
            y2 = self.height - y
            yOrigin = y

        region = self.__tiff.crop((x1, y1, x2, y2))
        background = self.__background.copy()
        background.paste(region, (xOrigin, yOrigin))
        return background

    def saveAs(self, tiffFileName):
        directory = os.path.splitext(self.tiffFileName)[0] + "/"
        if not os.path.exists(directory):
            os.mkdir(directory)
        tLength = len(str(self.T))
        zLength = len(str(self.Z))
        cLength = len(str(self.channels))
        i = 1
        for tIndex in range(0, self.T):
            for zIndex in range(0, self.Z):
                for channel in range(0, self.channels):
                    fileName = (
                        directory
                        + str(tIndex).zfill(tLength)
                        + "_"
                        + str(zIndex).zfill(zLength)
                        + "_"
                        + str(channel).zfill(cLength)
                        + ".tif"
                    )

                    i += 1
                    self.set_index(t=tIndex, z=zIndex, c=channel)
                    self.adjust().save(fileName)
        return True

    def save(self):
        self.saveAs(self.tiffFileName)
        return True

import tempfile

import numpy
from heronpy.api.bolt.bolt import Bolt

from scipy.misc import imsave
import os.path as op

class SaveImageToFileBolt(Bolt):
    outputs = ['path']

    def initialize(self, config, context):
        self.dir = tempfile.mkdtemp()
        self.log("Initializing SaveImageToFileBolt with dir {}".format(self.dir))
        self.file_name = "{version}_{from_y:03d}_{to_y:03d}.png"
        self.total_file_name = "{version}.png"
        self.totals = {}

    def process(self, tup):
        (version, image, y) = tup.values
        file_name = self.file_name.format(version=version, from_y=y, to_y=(y+image.shape[0]))
        path = op.join(self.dir, file_name)
        imsave(path, image)

        if version in self.totals:
            self.totals[version] = numpy.concatenate((self.totals[version], image))
        else:
            self.totals[version] = image

        total_path = op.join(self.dir, self.total_file_name.format(version=version))
        imsave(total_path, self.totals[version])

        self.emit([path])

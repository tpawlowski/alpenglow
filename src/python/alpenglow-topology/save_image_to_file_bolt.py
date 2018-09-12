import tempfile

from heronpy.api.bolt.bolt import Bolt

from scipy.misc import imsave
import os.path as op

class SaveImageToFileBolt(Bolt):
    outputs = ['path']

    def initialize(self, config, context):
        self.dir = tempfile.mkdtemp()
        self.log("Initializing SaveImageToFileBolt with dir {}".format(self.dir))
        self.file_name = "{version}_{from_y:03d}_{to_y:03d}.png"

    def process(self, tup):
        from_y, to_y, image3d = tup.values
        for version in range(image3d.shape[0]):
            file_name = self.file_name.format(version=version, from_y=from_y, to_y=to_y)
            path = op.join(self.dir, file_name)
            imsave(path, image3d[version, :, :])
            self.emit([path])

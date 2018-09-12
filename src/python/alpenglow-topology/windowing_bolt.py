import numpy
from heronpy.api.bolt.bolt import Bolt

from alpenglow.benchmark import BenchmarkConfig


class WindowingBolt(Bolt):
    outputs = ['from', 'to', 'image3d']

    def initialize(self, config, context):
        self.config = BenchmarkConfig.from_dict(config["benchmark_config"])
        self.data = {}
        self.window_offset = 0  # offset of next printed
        self.current_fill = 0  # up to where we have all versions already available
        self.first_offset = 0  # first offset containing still valid data.


    def process(self, tup):
        (version, image, y) = tup.values
        self.log("received {} {} {}".format(version, image.shape, y))

        if not self.data.has_key(y):
            self.data[y] = {}

        self.data[y][version] = image

        while len(self.data.get(self.current_fill, {})) == self.config.version_count:
            self.current_fill += self.data[self.current_fill][0].shape[0]
            self.log("filled up to {}".format(self.current_fill))

        while self.window_offset + self.config.window_length <= self.current_fill:
            self.log("emitting window [{}, {})".format(self.window_offset, self.window_offset + self.config.window_length))
            sample_image = self.data[self.first_offset][0]
            window = numpy.empty((self.config.version_count, self.config.window_length, sample_image.shape[1]),
                                 dtype=sample_image.dtype)

            window_fill = 0
            data_offset = self.first_offset

            while window_fill < self.config.window_length:
                layer_height = self.data[data_offset][0].shape[0]
                pixels_from = max(data_offset, self.window_offset) - data_offset
                pixels_to = min(self.window_offset + self.config.window_length - data_offset, layer_height)

                for version, image in self.data[data_offset].items():
                    window[version, window_fill:(window_fill + pixels_to - pixels_from), :] = image[pixels_from:pixels_to, :]

                window_fill += pixels_to - pixels_from
                data_offset += layer_height

            self.emit([self.window_offset, self.window_offset + self.config.window_length, window])

            self.window_offset += self.config.window_step

            # clean used data
            while self.first_offset < self.window_offset and self.first_offset + self.data[self.first_offset][0].shape[0] <= self.window_offset:
                layer_height = self.data[self.first_offset][0].shape[0]
                self.log("releasing data [{}, {})".format(self.first_offset, self.first_offset + layer_height))
                del self.data[self.first_offset]
                self.first_offset += layer_height




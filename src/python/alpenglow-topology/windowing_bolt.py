import sys

from heronpy.api.bolt.bolt import Bolt

from alpenglow.benchmark import BenchmarkConfig, WindowState


class WindowingBolt(Bolt):
    outputs = ['from', 'to', 'image3d']

    def initialize(self, config, context):
        self.config = BenchmarkConfig.from_dict(config["benchmark_config"])
        if self.config.verbosity > 0:
            self.log("Initializing WindowingBolt...")
        self.state = WindowState(self.config)


    def process(self, tup):
        (version, image, y) = tup.values
        if self.config.verbosity > 1:
            self.log("received {} {} {}".format(version, image.shape, y))
        results = self.state.apply(version, image, y)
        for result in results:
            if self.config.verbosity > 0:
                self.log("emitting [{}, {}) mem usage: {}".format(result[0], result[1], sys.getsizeof(self.state)))
            self.emit(result)

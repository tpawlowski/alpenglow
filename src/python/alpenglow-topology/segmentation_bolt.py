from heronpy.api.bolt.bolt import Bolt

from alpenglow.benchmark import segmentation, BenchmarkConfig


class SegmentationBolt(Bolt):
    outputs = ['from', 'to', 'mask']

    def initialize(self, config, context):
        self.config = BenchmarkConfig.from_dict(config["benchmark_config"])
        if self.config.verbosity > 0:
            self.log("Initializing SegmentationBolt...")

    def process(self, tup):
        (from_y, to_y, image) = tup.values
        if self.config.verbosity > 0:
            self.log("running segmentation on image [{}, {})".format(from_y, to_y))
        self.emit([from_y, to_y, segmentation(image)])

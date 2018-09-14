from heronpy.api.bolt.bolt import Bolt

from alpenglow.benchmark import validate, BenchmarkConfig


class ValidationBolt(Bolt):
    outputs = ['from', 'to', 'validation']

    def initialize(self, config, context):
        self.config = BenchmarkConfig.from_dict(config["benchmark_config"])
        if self.config.verbosity > 0:
            self.log("Initializing ValidationBolt...")

    def process(self, tup):
        (from_y, to_y, mask) = tup.values
        h = validate(mask)
        if self.config.verbosity > 0:
            self.log("validated image [{}, {}): {}".format(from_y, to_y, h))
        self.emit([from_y, to_y, h])

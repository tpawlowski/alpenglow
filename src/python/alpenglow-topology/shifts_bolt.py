from alpenglow.benchmark import ShiftState, BenchmarkConfig
from heronpy.api.bolt.bolt import Bolt


class ShiftsBolt(Bolt):
    outputs = ['stripe', 'shift', 'shape']

    def initialize(self, config, context):
        self.log("Initializing ShiftsBolt...")
        self.config = BenchmarkConfig.from_dict(config["benchmark_config"])
        self.state = ShiftState(self.config)

    def process(self, tup):
        (stripe, correlation, top_shape) = tup.values

        if self.config.verbosity > 0:
            self.log("received {}".format(stripe))

        shift = self.state.apply(stripe, correlation, top_shape)
        if shift is not None:
            if self.config.verbosity > 0:
                self.log("emmiting {}".format(shift))
            self.emit(shift)

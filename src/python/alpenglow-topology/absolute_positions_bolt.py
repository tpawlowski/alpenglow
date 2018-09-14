from heronpy.api.bolt.bolt import Bolt

from alpenglow.benchmark import BenchmarkConfig, PositionState, get_image_source


class AbsolutePositionsBolt(Bolt):
    outputs = ['version', 'stripe', 'x', 'y', 'width', 'top_overlay', 'bottom_overlay', 'shift']

    def initialize(self, config, context):
        self.log("Initializing AbsolutePositionsBolt...")
        self.config = BenchmarkConfig.from_dict(config["benchmark_config"])
        self.state = PositionState(self.config)
        self.version_count = get_image_source(self.config).version_count()

    def process(self, tup):
        if self.config.verbosity > 0:
            self.log("received shift: {}".format(tup.values))

        (stripe, shift, shape) = tup.values
        for position in self.state.apply(stripe, shift, shape):
            if self.config.verbosity > 0:
                self.log("broadcasting position: {}".format(position))

            for version in range(self.version_count):
                self.emit([version] + list(position))

from alpenglow.benchmark import CorrelationState, BenchmarkConfig
from heronpy.api.bolt.bolt import Bolt


class CorrelationsBolt(Bolt):
    outputs = ['stripe', 'correlation_matrix', 'top_image_shape']

    def initialize(self, config, context):
        self.log("Initializing CountCorrelationsBolt...")
        self.config = BenchmarkConfig.from_dict(config["benchmark_config"])
        self.state = CorrelationState(self.config)

    def process(self, tup):
        (stripe, version, image) = tup.values
        if self.config.verbosity > 0:
            self.log("received {}".format(tup.values))

        for correlation in self.state.apply(version, stripe, image):
            if self.config.verbosity > 0:
                self.log("emitting {}".format(correlation))
            self.emit(correlation)

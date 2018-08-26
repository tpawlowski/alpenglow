from heronpy.api.bolt.bolt import Bolt

from alpenglow.benchmark import is_in_sample, BenchmarkConfig


class SamplingBolt(Bolt):
    outputs = ['stripe', 'version']

    def initialize(self, config, context):
        self.log("Initializing SamplingBolt...")
        self.config = BenchmarkConfig.from_dict(config["benchmark_config"])

    def process(self, tup):
        stripe, version = tup.values

        if self.config.verbosity > 0:
            self.log("got pair {}".format((stripe, version)))

        if is_in_sample(self.config, version):
            if self.config.verbosity > 0:
                self.log("accepting {}".format((stripe, version)))
            self.emit(tup.values)

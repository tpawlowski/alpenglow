from heronpy.api.bolt.bolt import Bolt

from alpenglow.benchmark import BenchmarkConfig, MergeImageState


class OutputImageBolt(Bolt):
    outputs = ['version', 'image', 'y']

    def initialize(self, config, context):
        self.config = BenchmarkConfig.from_dict(config["benchmark_config"])
        if self.config.verbosity > 0:
            self.log("Initializing AbsolutePositionsBolt...")
        self.state = MergeImageState(self.config)

    def process(self, tup):
        to_emit = []
        if len(tup.values) == 3:
            (stripe, version, image) = tup.values
            if self.config.verbosity > 1:
                self.log("got image version: {} stripe: {}".format(version, stripe))
            to_emit.extend(self.state.apply_image(version, stripe, image))
        else:
            if self.config.verbosity > 0:
                self.log("got metadata version: {} stripe: {}".format(tup.values[0], tup.values[1]))
            to_emit.extend(self.state.apply_metadata(tup.values))

        for image in to_emit:
            if self.config.verbosity > 0:
                self.log("emitting version: {} y: {}".format(image[0], image[2]))
            self.emit(image)


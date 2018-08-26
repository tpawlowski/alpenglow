from heronpy.api.bolt.bolt import Bolt

from alpenglow.benchmark import get_image_source, BenchmarkConfig


class GetDemoImageBolt(Bolt):
    outputs = ['stripe', 'version', 'image']

    def initialize(self, config, context):
        self.log("Initializing GetDemoImageBolt...")
        self.config = BenchmarkConfig.from_dict(config["benchmark_config"])
        self.image_source = get_image_source(self.config)

    def process(self, tup):
        stripe, version = tup.values
        if self.config.verbosity > 0:
            self.log("request {}".format((version, stripe)))
        image = self.image_source.get_image(stripe, version)
        self.emit([stripe, version, image])

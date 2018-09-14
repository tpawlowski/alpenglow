from heronpy.api.bolt.bolt import Bolt

from alpenglow.benchmark import BenchmarkConfig, DelayDownloadState


class DelayImageDownloadBolt(Bolt):
    outputs = ['stripe', 'version']

    def initialize(self, config, context):
        self.config = BenchmarkConfig.from_dict(config["benchmark_config"])
        if self.config.verbosity > 0:
            self.log("Initializing  DelayImageDownload...")
        self.state = DelayDownloadState(self.config)

    def process(self, tup):
        if len(tup.values) == 2:
            stripe, version = tup.values
            if self.state.apply_image_id(stripe, version):
                self.emit([stripe, version])
        else:
            version = tup.values[0]
            stripe = tup.values[1]
            if self.state.apply_metadata(stripe, version):
                self.emit([stripe, version])


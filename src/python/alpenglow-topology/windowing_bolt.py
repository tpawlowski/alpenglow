from heronpy.api.bolt.bolt import Bolt

from alpenglow.benchmark import BenchmarkConfig, WindowState


class WindowingBolt(Bolt):
    outputs = ['from', 'to', 'image3d']

    def initialize(self, config, context):
        self.config = BenchmarkConfig.from_dict(config["benchmark_config"])
        self.state = WindowState(self.config)


    def process(self, tup):
        (version, image, y) = tup.values
        self.log("received {} {} {}".format(version, image.shape, y))
        results = self.state.apply(version, image, y)
        for result in results:
            self.log("emitting [{}, {})".format(result[0], result[1]))
            self.emit(result)

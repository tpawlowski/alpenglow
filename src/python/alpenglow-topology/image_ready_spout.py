from alpenglow.benchmark import get_image_order, BenchmarkConfig
from heronpy.api.spout.spout import Spout


class ImageReadySpout(Spout):
    """
    Spout emitting pairs which indicate that image is ready for download

    In demo case all images are available from the beginning.
    """
    outputs = ['stripe', 'version']

    def initialize(self, config, context):
        self.generator = get_image_order(BenchmarkConfig.from_dict(config["benchmark_config"]))
        self.failed = []

    def next_tuple(self):
        if len(self.failed) > 0:
            tup_id = self.failed.pop()
            self.log("re-emitting {}".format(tup_id))
            self.emit([tup_id[0], tup_id[1]], tup_id=tup_id)
        else:
            try:
                tup_id = self.generator.next()
                self.log("emit {}".format(tup_id))
                self.emit([tup_id[0], tup_id[1]], tup_id=tup_id)
            except StopIteration:
                pass

    def fail(self, tup_id):
        self.log("received fail {}".format(tup_id))
        self.failed.append(tup_id)





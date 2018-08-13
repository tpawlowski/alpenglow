from heronpy.api.bolt.bolt import Bolt

from alpenglow.image_sources.demo import DemoImageSource


class GetDemoImageBolt(Bolt):
    outputs = ['version', 'stripe', 'image']

    def initialize(self, config, context):
        self.image_source = DemoImageSource(**config['image_source_config'])
        self.log("Initializing GetDemoImageBolt...")

    def process(self, tup):
        (version, stripe) = tup.values
        self.log("request {}".format((version, stripe)))
        image = self.image_source.get_image(stripe, version)
        self.emit([version, stripe, image])

from heronpy.api.spout.spout import Spout


class ImageReadySpout(Spout):
    """
    Spout emitting pairs which indicate that image is ready for download

    In demo case all images are available from the beginning.
    """
    outputs = ['version', 'stripe']

    def initialize(self, config, context):
        self.version_count = config['version_count']
        self.stripe_count = config['stripe_count']
        self.log("Initializing Image Ready Spout with versions {} and stripes {}".format(self.version_count, self.stripe_count))

        self.version = 0
        self.stripe = 0
        self.failed = []

    def next_tuple(self):
        if len(self.failed) > 0:
            tup_id = self.failed.pop()
            self.log("received fail {}".format(tup_id))
            self.emit([tup_id[0], tup_id[1]], tup_id=tup_id)
        elif self.version < self.version_count and self.stripe < self.stripe_count:
            tup_id = (self.version, self.stripe)
            self.log("emit {}".format(tup_id))
            self.emit([self.version, self.stripe], tup_id=tup_id)
            self.version += 1

            if self.version >= self.version_count:
                self.version = 0
                self.stripe += 1

    def fail(self, tup_id):
        self.log("received fail {}".format(tup_id))
        self.failed.append(tup_id)





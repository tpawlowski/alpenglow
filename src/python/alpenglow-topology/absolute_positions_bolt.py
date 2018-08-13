from heronpy.api.bolt.bolt import Bolt


class AbsolutePositionsBolt(Bolt):
    outputs = ['version', 'stripe', 'x', 'y', 'width', 'top_overlay', 'bottom_overlay', 'shift']

    def initialize(self, config, context):
        self.log("Initializing AbsolutePositionsBolt...")
        self.margin = config["margin"]
        self.version_count = config["version_count"]
        self.waiting = {}

        self.current = None
        self.width = None
        self.x = config["margin"]
        self.y = 0
        self.previous_overlay = 0

    def process(self, tup):
        (stripe, shift, shape) = tup.values

        if self.current is None:
            self.current = stripe
            self.width = 2 * self.margin + shape[1]

        if stripe >= self.current:
            self.log("saving stripe {}".format(stripe))
            self.waiting[stripe] = (shift, shape)
        else:
            self.log("saving delayed skipping {}".format(stripe))

        while self.current in self.waiting:
            (shift, shape) = self.waiting[self.current]
            del self.waiting[self.current]
            self.log("emitting {}".format(self.current))
            for version in range(self.version_count):
                self.emit([version, self.current, self.x, self.y, self.width, self.previous_overlay, shift[0], shift[1]])
            self.x += shift[1]
            self.y += shape[0] - shift[0]
            self.previous_overlay = shift[0]
            self.current += 1

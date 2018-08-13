from heronpy.api.bolt.bolt import Bolt

from alpenglow.matching_algorithms.fft import FftMatchingAlgorithm


class CorrelationsBolt(Bolt):
    outputs = ['version', 'stripe', 'correlation_matrix', 'top_shape', 'bottom_shape']

    def initialize(self, config, context):
        self.log("Initializing CountCorrelationsBolt...")
        self.first_stripe = None
        self.bottoms = {}
        self.tops = {}

    def process(self, tup):
        (version, stripe, image) = tup.values
        self.log("request {}".format((version, stripe)))

        if self.first_stripe is None:
            self.log("setting first stripe to {}".format(stripe))
            self.first_stripe = stripe

        if stripe > self.first_stripe:
            top_id = (version, stripe - 1)
            if top_id in self.tops:
                top_image = self.tops[top_id]
                del self.tops[top_id]
                self.emit_correlation(version, stripe - 1, top_image, image)
            else:
                self.log("{} waiting for {}".format((version, stripe), top_id))
                self.bottoms[(version, stripe)] = image

        bottom_id = (version, stripe + 1)
        if bottom_id in self.bottoms:
            bottom_image = self.bottoms[bottom_id]
            del self.bottoms[bottom_id]
            self.emit_correlation(version, stripe, image, bottom_image)
        else:
            self.log("{} waiting for {}".format((version, stripe), bottom_id))
            self.tops[(version, stripe)] = image

    def emit_correlation(self, version, stripe, top_image, bottom_image):
        self.log("emitting correlation for {}".format((version, stripe)))
        width = min(top_image.shape[1], bottom_image.shape[1])
        height = min(top_image.shape[0], bottom_image.shape[0]) // 2

        correlation = FftMatchingAlgorithm.cross_correlation(top_image[-height:, :width], bottom_image[:height, :width])

        self.emit([version, stripe, correlation, top_image.shape, bottom_image.shape])

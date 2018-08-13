from heronpy.api.bolt.bolt import Bolt

import numpy


class ShiftsBolt(Bolt):
    outputs = ['stripe', 'shift', 'shape']

    def initialize(self, config, context):
        self.log("Initializing ShiftsBolt...")
        self.sample_size = config["sample_size"]
        self.sums = {}

    def process(self, tup):
        (version, stripe, correlation, top_shape, bottom_shape) = tup.values

        if stripe not in self.sums:
            self.sums[stripe] = (correlation, 1)
        else:
            old_correlation, cnt = self.sums[stripe]
            self.sums[stripe] = (correlation + old_correlation, cnt + 1)

        if self.sums[stripe][1] == self.sample_size:
            correlation = self.sums[stripe][0]
            del self.sums[stripe]
            self.emit_shift(stripe, correlation, top_shape)

    def emit_shift(self, stripe, correlation, shape):
        midpoints = numpy.array([numpy.fix(axis_size / 2) for axis_size in correlation.shape])
        maxima = numpy.unravel_index(numpy.argmax(numpy.abs(correlation)), correlation.shape)
        shifts = numpy.array(maxima, dtype=numpy.int)

        shifts[shifts > midpoints] -= numpy.array(correlation.shape)[shifts > midpoints]
        shifts[0] = correlation.shape[0] - shifts[0]

        self.log("emit {}".format([stripe, list(shifts)]))
        self.emit([stripe, list(shifts), shape])

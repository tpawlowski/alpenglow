from heronpy.api.bolt.bolt import Bolt


class SamplingBolt(Bolt):
    outputs = ['version', 'stripe']

    def initialize(self, config, context):
        self.version_count = config['version_count']
        self.sample_size = config['sample_size']
        self.log("Initializing SamplingBolt...")

    def process(self, tup):
        (version, stripe) = tup.values
        self.log("got pair {}".format((version, stripe)))
        if self.__check(version):
            self.log("accepting {}".format((version, stripe)))
            self.emit([version, stripe])

    def __check(self, version):
        if self.sample_size == 1:  # accept middle one
            return version == self.version_count // 2
        elif self.sample_size == 2:  # accept edges
            return version == 0 or version == self.version_count - 1
        else:  # accept evenly distributed versions
            return (version == 0) or \
                   (((version + 1) * (self.sample_size - 1)) % self.version_count) == 0 or \
                   (version + 1) * (self.sample_size - 1) // self.version_count > version * (self.sample_size - 1) // self.version_count

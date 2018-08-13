from heronpy.api.bolt.bolt import Bolt

import numpy

from alpenglow.patchwork_builders.default import PatchworkBuilder


class OutputImageBolt(Bolt):
    outputs = ['version', 'image', 'y']

    def initialize(self, config, context):
        self.log("Initializing AbsolutePositionsBolt...")
        self.image_buffer = {}
        self.metadata_buffer = {}
        self.current = {}

    def process(self, tup):
        if len(tup.values) == 3:
            (version, stripe, image) = tup.values
            self.log("got image version: {} stripe: {}".format(version, stripe))
            self.process_image(version, stripe, image)
        else:
            self.log("got metadata version: {} stripe: {}".format(tup.values[0], tup.values[1]))
            self.process_metadata(tup.values)

    def process_image(self, version, stripe, image):
        if version not in self.image_buffer:
            self.image_buffer[version] = {}
        if version not in self.metadata_buffer:
            self.metadata_buffer[version] = {}
            self.current[version] = (stripe, False)

        self.image_buffer[version][stripe] = image

        self.try_emit(version)

    def process_metadata(self, tup):
        version = tup[0]
        stripe = tup[1]

        if version not in self.metadata_buffer:
            self.metadata_buffer[version] = {}
            self.current[version] = (stripe, False)
        if version not in self.image_buffer:
            self.image_buffer[version] = {}

        self.metadata_buffer[version][stripe] = tup[2:]

        self.try_emit(version)

    def try_emit(self, version):
        while True:
            (current_stripe, top_printed) = self.current[version]

            if top_printed:
                if current_stripe in self.metadata_buffer[version]\
                        and current_stripe in self.image_buffer[version]\
                        and (current_stripe + 1) in self.image_buffer[version]:
                    self.emit_overlay(version,
                                      self.metadata_buffer[version][current_stripe],
                                      self.image_buffer[version][current_stripe],
                                      self.image_buffer[version][current_stripe + 1])
                    del self.metadata_buffer[version][current_stripe]
                    del self.image_buffer[version][current_stripe]
                    self.current[version] = (current_stripe + 1, False)
                else:
                    break
            else:
                if current_stripe in self.metadata_buffer[version]\
                        and current_stripe in self.image_buffer[version]:
                    self.emit_uniq(version,
                                   self.metadata_buffer[version][current_stripe],
                                   self.image_buffer[version][current_stripe])
                    self.current[version] = (current_stripe, True)
                else:
                    break

    def emit_uniq(self, version, metadata, image):
        (x, y, width, top_overlay, bottom_overlay, _) = metadata
        height = image.shape[0] - top_overlay - bottom_overlay
        data = numpy.zeros((height, width), dtype=image.dtype)
        data[:, max(x, 0):min(x + image.shape[1], width)] = image[top_overlay:-bottom_overlay, max(-x, 0):min(image.shape[1], width - x)]

        self.log("emit [{},{}) from {} uniq".format(y + top_overlay, y + top_overlay + data.shape[0], version))
        self.emit([version, data, y + top_overlay])

    def emit_overlay(self, version, metadata, top_image, bottom_image):
        (x, y, width, _, overlay, shift) = metadata
        height = overlay
        data = numpy.zeros((height, width), dtype=top_image.dtype)

        data[:, max(x, 0):min(x + top_image.shape[1], width)] = top_image[-overlay:, max(-x, 0):min(top_image.shape[1], width - x)]
        bottom_x = x + shift
        data[:, max(bottom_x, 0):min(bottom_x + bottom_image.shape[1], width)] =\
            PatchworkBuilder.gradient_merge_arrays(
                data[:, max(bottom_x, 0):min(bottom_x + bottom_image.shape[1], width)],
                bottom_image[:overlay, max(-bottom_x, 0):min(bottom_image.shape[1], width - bottom_x)])

        self.log("emit [{},{}) from {} overlay".format(y + top_image.shape[0] - overlay, y + top_image.shape[0], version))
        self.emit([version, data, y + top_image.shape[0] - overlay])

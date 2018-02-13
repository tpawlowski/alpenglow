import os
import tempfile

import numpy
from time import time

from alpenglow.memory_mapped_stripe import MemoryMappedStripe


class PatchworkBuilder:
    """
    Representation of an image stitched from multiple stripes.
    """
    def __init__(self, matching_algorithm):
        """
        Parameters
        ----------
        matching_algorithm: MatchingAlgorithm
            MatchingAlgorithm used by the builder to detect common part and horizontal shift between each pair of
            consecutive stripes.
        """
        self.matching_algorithm = matching_algorithm

        self.patchwork = []

        self.stitching_times = []
        self.result_building_time = None

    def stitch(self, stripe):
        """
        Stitches stripe on the bottom of the represented patchwork.

        Parameters
        ----------
        stripe: Stripe

        Raises
        -------
        StitchingMismatchException
            Raised when matching of stripe to current patchwork fails.
        """
        stitching_start_time = time()
        if len(self.patchwork) == 0:
            self.patchwork.append((stripe, (0, 0)))
            self.stitching_times.append(time() - stitching_start_time)
            return

        last_stripe, last_shift = self.patchwork[-1]

        relative_shift = self.matching_algorithm.match(last_stripe, stripe)

        shift = (relative_shift[0], last_shift[1] + relative_shift[1])
        self.patchwork.append((stripe, shift))
        self.stitching_times.append(time() - stitching_start_time)

    def get(self):
        """
        Returns
        -------
        stripe: MemoryMappedStripe
            Memory mapped stripe created from all stitched stripes.
        """
        result_building_start_time = time()
        if len(self.patchwork) == 0:
            raise IndexError('No stripes were added to the patchwork')

        first_stripe = self.patchwork[0][0]

        channel_height = sum([stripe.get_channel_shape()[0] - shift[0] for stripe, shift in self.patchwork])
        total_height = channel_height * first_stripe.channel_count()
        total_width = first_stripe.get_shape()[1]
        version_count = first_stripe.version_count()

        filename = os.path.join(tempfile.mkdtemp(), 'stripe.dat')
        data = numpy.memmap(filename, mode='w+', dtype=first_stripe.get_dtype(),
                            shape=(version_count, total_height, total_width))

        current_height = 0
        for stripe, shift in self.patchwork:
            row_from = current_height - shift[0]
            row_to = row_from + stripe.get_channel_shape()[0]
            column_from = max(0, shift[1])
            column_to = min(total_width, shift[1] + stripe.get_shape()[1])

            for channel_id in range(first_stripe.channel_count()):
                channel_offset = channel_id * channel_height
                for version_id in range(version_count):
                    image_to_paste = stripe.get_channel_image(version_id, channel_id)[:, max(0, -shift[1]):min(total_width - shift[1], stripe.get_shape()[1])]

                    if shift[0] > 0:
                        data[version_id, (channel_offset + row_from):(channel_offset + current_height), column_from:column_to] = \
                            self.__class__.gradient_merge_arrays(data[version_id, (channel_offset + row_from):(channel_offset + current_height), column_from:column_to], image_to_paste[0:shift[0], :])
                        data[version_id, (channel_offset + current_height):(channel_offset + row_to), column_from:column_to] = image_to_paste[shift[0]:, :]
                    else:
                        data[version_id, (channel_offset + row_from):(channel_offset + row_to), column_from:column_to] = image_to_paste

            current_height = row_to

        self.result_building_time = time() - result_building_start_time
        return MemoryMappedStripe(data, first_stripe.channel_count())

    def benchmark(self):
        """

        Returns
        -------
        stitching_times: [float]
            Times in seconds taken for stitching nth stripe (fetching required images + matching).
        result_building: float
            Time in seconds taken for building resulting 3D array based on matches.
        """
        return self.stitching_times, self.result_building_time

    @classmethod
    def gradient_merge_arrays(cls, image_one, image_two):
        """
        Merges two images together, by linearly (from top to bottom) increasing transparency of image_one and
        decreasing transparency of image_two.

        Parameters
        ----------
        image_one: np.array
        image_two: np.array

        Returns
        -------
        image: np.array
            array created by combining two source images.
        """
        height = image_one.shape[0]
        vector_one = numpy.array([1.0 - (i + 1) / (height + 1) for i in range(height)])
        vector_two = numpy.array([(i + 1) / (height + 1) for i in range(height)])
        return (image_one * vector_one[:, numpy.newaxis]) + (image_two * vector_two[:, numpy.newaxis])

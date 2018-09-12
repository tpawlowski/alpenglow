import concurrent

import numpy
from time import time

from alpenglow.stripes.memory_mapped import MemoryMappedStripe
from alpenglow.patchwork_builders.default import PatchworkBuilder


class StreamingPatchworkBuilder:
    """
    Patchwork builder returning parts of image while during stitching process.
    """
    def __init__(self, matching_algorithm, margin=0):
        """
        Parameters
        ----------
        matching_algorithm: MatchingAlgorithm
            MatchingAlgorithm used by the builder to detect common part and horizontal shift between each pair of
            consecutive stripes.
        margin: int
            Number of pixels appended from both sides (left, right) to first stripe to cover horizontal shifts of
            upcoming stripes
        """
        self.matching_algorithm = matching_algorithm
        self.margin = margin
        self.channel_width = None

        self.patchwork = []

        self.stitching_times = []
        self.result_building_times = []

        self.image_cache = None

    def stitch(self, stripe):
        """
        Stitches stripe on the bottom of the represented patchwork.

        Parameters
        ----------
        stripe: Stripe

        Returns
        -------
        stripe: MemoryMappedStripe
            memory mapped stripe containing part of final image which is already fixed.

        Raises
        -------
        StitchingMismatchException
            Raised when matching of stripe to current patchwork fails.
        """
        stitching_start_time = time()

        if len(self.patchwork) == 0:
            self.patchwork.append((stripe, (0, self.margin)))
            self.channel_width = stripe.get_channel_shape()[1] + 2 * self.margin

            shape = (stripe.version_count(), 0, stripe.channel_count() * self.channel_width)
            data = numpy.empty(shape, stripe.get_dtype())
            empty_data = MemoryMappedStripe(data, stripe.channel_count())
            self.stitching_times.append(time() - stitching_start_time)
            return empty_data
        else:
            last_stripe, last_shift = self.patchwork[-1]

            relative_shift = self.matching_algorithm.match(last_stripe, stripe)

            print("relative shift: {} stripe height: {}".format(relative_shift, stripe.get_channel_shape()))

            shift = (relative_shift[0], last_shift[1] + relative_shift[1])
            self.patchwork.append((stripe, shift))
            if len(self.patchwork) > 2:
                self.patchwork[-2] = None  # saves memory

            self.stitching_times.append(time() - stitching_start_time)
            return self.get_newly_fixed(last_stripe, last_shift, stripe, shift)

    def get_newly_fixed(self, previous_stripe, previous_shift, stripe, shift):
        """
        Calculates part of final image which becomes fixed, e.g. won't be affected by adding next stripes, after adding
        last stripe.

        Parameters
        ----------
        previous_stripe: Stripe
            semi last stripe
        previous_shift: tuple(int)
            number of pixels from top already printed,
            horizontal shift from left edge
        stripe: Stripe
            last stripe
        shift: tuple(int)
            number of pixels in vertical where last and semi last stripe overlap,
            horizontal shift from left edge

        Returns
        -------
        stripe: MemoryMappedStripe
            Memory mapped stripe with all rows which were fixed after adding last stripe. That is rows from semi last
            stripe, excluding already printed rows, up to rows common to semi last and last stripe.
        """
        result_building_start_time = time()

        channel_count = previous_stripe.channel_count()
        version_count = previous_stripe.version_count()
        height = previous_stripe.get_channel_shape()[0] - previous_shift[0]
        total_width = self.channel_width * channel_count

        data = numpy.zeros((version_count, height, total_width), dtype=previous_stripe.get_dtype())

        # fetch rows from previous stripe (if they are not in cache)
        if self.image_cache is None:
            self.image_cache = {}
            future_images = {}
            for version_id in range(version_count):
                future_images[previous_stripe.get_image_future(version_id)] = version_id
            for future_image in concurrent.futures.as_completed(future_images):
                self.image_cache[future_images[future_image]] = future_image.result()

        # include previous stripe in the result
        for version_id in range(version_count):
            previous_channel_width = previous_stripe.get_channel_shape()[1]

            row_from = previous_shift[0]
            row_to = previous_stripe.get_channel_shape()[0]

            column_from = max(previous_shift[1], 0)
            column_to = min(self.channel_width, previous_shift[1] + previous_stripe.get_channel_shape()[1])

            image = self.image_cache[version_id]
            for channel_id in range(channel_count):
                channel_offset = channel_id * self.channel_width

                data[version_id, 0:(row_to - row_from), (channel_offset + column_from):(channel_offset + column_to)] =\
                    image[row_from:row_to, (channel_id * previous_channel_width + max(0, -previous_shift[1])):(channel_id * previous_channel_width + max(0, -previous_shift[1]) + column_to - column_from)]

        if shift[0] == 0:
            self.image_cache = None
        else:
            future_images = {}
            for version_id in range(version_count):
                future_images[stripe.get_image_future(version_id)] = version_id

            for future_image in concurrent.futures.as_completed(future_images):
                version_id = future_images[future_image]
                self.image_cache[version_id] = future_image.result()

                for channel_id in range(channel_count):
                    channel_offset = channel_id * self.channel_width
                    stripe_width = stripe.get_channel_shape()[1]
                    column_from = max(shift[1], 0)
                    column_to = min(self.channel_width, shift[1] + stripe.get_channel_shape()[1])

                    image_to_paste = future_image.result()[0:shift[0], (channel_id * stripe_width + max(0, -shift[1])):(channel_id * stripe_width + max(0, -shift[1]) + column_to - column_from)]

                    data[version_id, (height - shift[0]):height, (channel_offset + column_from):(channel_offset + column_to)] = \
                        PatchworkBuilder.gradient_merge_arrays(
                            data[version_id, (height - shift[0]):height, (channel_offset + column_from):(channel_offset + column_to)],
                            image_to_paste)

        result = MemoryMappedStripe(data, channel_count)
        self.result_building_times.append(time() - result_building_start_time)
        return result

    def get(self):
        """
        Returns
        -------
        stripe: MemoryMappedStripe
            Remaining non fixed part
        """
        if len(self.patchwork) == 0:
            raise IndexError('No stripes were added to the patchwork')

        previous_stripe, previous_shift = self.patchwork[-1]
        return self.get_newly_fixed(previous_stripe, previous_shift, None, (0, 0))

    def benchmark(self):
        """

        Returns
        -------
        stitching_times: [float]
            Times in seconds taken for stitching nth stripe (fetching required images + matching).
        result_building: [float]
            Time in seconds taken for building resulting 3D array based on matches.
        """
        return self.stitching_times, self.result_building_times

import concurrent

import numpy
import os
import tempfile
from time import time


from alpenglow.patchwork_builders.default import PatchworkBuilder


class LazyStitchedData:
    def __init__(self, patchwork):
        self.patchwork = patchwork

        first_stripe = patchwork[0][0]
        self.channel_count = first_stripe.channel_count()
        self.total_height = sum([stripe.get_channel_shape()[0] - shift[0] for stripe, shift in patchwork])
        self.channel_width = first_stripe.get_channel_shape()[1]
        self.total_width = self.channel_width * self.channel_count
        self.version_count = first_stripe.version_count()

        filename = os.path.join(tempfile.mkdtemp(), 'stripe.dat')
        self.data = numpy.memmap(filename, mode='w+', dtype=first_stripe.get_dtype(),
                            shape=(self.version_count, self.total_height, self.total_width))
        self.mask = numpy.zeros(self.version_count, dtype=numpy.bool)

    def __getitem__(self, arg):
        if isinstance(arg, int):
            self.__download(range(arg, arg+1))
        elif isinstance(arg, slice):
            self.__download(list(range(self.version_count))[arg])
        elif isinstance(arg, tuple):
            if isinstance(arg[0], int):
                self.__download(range(arg[0], arg[0]+1))
            elif isinstance(arg[0], slice):
                self.__download(list(range(self.version_count))[arg[0]])

        return self.data[arg]

    def __getslice__(self, start, end):
        self.__download(range(start, end))
        return self.data[start:end]

    def __download(self, version_range):
        versions_to_fetch = []
        for version_id in version_range:
            if not self.mask[version_id]:
                versions_to_fetch.append(version_id)
                self.mask[version_id] = True

        if len(versions_to_fetch) == 0:
            return

        current_height = 0
        for stripe, shift in self.patchwork:
            row_from = current_height - shift[0]
            row_to = row_from + stripe.get_channel_shape()[0]

            stripe_channel_width = stripe.get_channel_shape()[1]
            column_from = max(0, shift[1])
            column_to = min(self.channel_width, shift[1] + stripe_channel_width)

            future_images = {}
            for version_id in versions_to_fetch:
                future_images[stripe.get_image_future(version_id)] = version_id

            for future_image in concurrent.futures.as_completed(future_images):
                version_id = future_images[future_image]

                for channel_id in range(self.channel_count):
                    channel_offset = channel_id * self.channel_width

                    image_to_paste = future_image.result()[:, (channel_id * stripe_channel_width + max(0, -shift[1])):(channel_id * stripe_channel_width + max(0, -shift[1]) + column_to - column_from)]

                    if shift[0] > 0:
                        self.data[version_id, (current_height - shift[0]):current_height, (channel_offset + column_from):(channel_offset + column_to)] = \
                            PatchworkBuilder.gradient_merge_arrays(
                                self.data[version_id, (current_height - shift[0]):current_height, (channel_offset + column_from):(channel_offset + column_to)],
                                image_to_paste[0:shift[0], :])
                        self.data[version_id, current_height:row_to, (channel_offset + column_from):(channel_offset + column_to)] = image_to_paste[shift[0]:, :]
                    else:
                        self.data[version_id, row_from:row_to, (channel_offset + column_from):(channel_offset + column_to)] = image_to_paste

            current_height = row_to


class LazyPatchworkBuilder:
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
        if len(self.patchwork) == 0:
            raise IndexError('No stripes were added to the patchwork')
        return LazyStitchedData(self.patchwork)

    def benchmark(self):
        """

        Returns
        -------
        stitching_times: [float]
            Times in seconds taken for stitching nth stripe (fetching required images + matching).
        """
        return self.stitching_times

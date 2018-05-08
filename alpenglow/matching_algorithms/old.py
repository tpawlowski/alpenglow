import numpy
from skimage.feature import register_translation

from alpenglow.matching_algorithms.matching_algorithm import MatchingAlgorithm


class StripeMismatchException(Exception):
    """
    Exception raised when stitching of stripe to patchwork fails.
    """
    pass


class OldMatchingAlgorithm(MatchingAlgorithm):
    """
    Implementation of stripe matching algorithm derived from file stitching2.py
    """
    def __init__(self, versions, channels):
        """
        Parameters
        ----------
        versions: [int]
            List of versions to test for shift
        channels: [int]
            List of channels to test for shift
        """
        if not versions:
            raise ValueError("Shift must be detected in at least one version of images")
        self._versions = versions

        if not channels:
            raise ValueError("Shift must be detected in at least one channel")
        self._channels = channels

    def match(self, top_stripe, bottom_stripe):
        self.__class__.validate_dimensions(top_stripe, bottom_stripe)

        measured_shifts = self.measure_shifts(top_stripe, bottom_stripe)
        shift = self.__class__.extract_shift(measured_shifts)
        self.__class__.validate_shift(shift, measured_shifts)

        return shift

    def measure_shifts(self, top_stripe, bottom_stripe):
        shifts = []

        for version_id in self._versions:
            for channel_id in self._channels:
                top_channel = top_stripe.get_channel_image(version_id, channel_id)
                bottom_channel = bottom_stripe.get_channel_image(version_id, channel_id)
                shifts.append(self.__class__.find_shift(top_channel, bottom_channel))

        return numpy.array(shifts, numpy.float)

    @classmethod
    def validate_shift(cls, final_shift, shifts):
        for index in [0, 1]:
            std = numpy.std(shifts[:, index] - final_shift[index])

            if any(abs(shift - final_shift[index]) > 3 * std + 1 for shift in shifts[:, index]):
                raise StripeMismatchException("Shift[{1}] in ({0}) is not around single value {2} with std {3}".format(shifts, index, final_shift[index], std))

    @classmethod
    def validate_dimensions(cls, top_stripe, bottom_stripe):
        if top_stripe.channel_count() != bottom_stripe.channel_count():
            raise ValueError("Stripes with different number of channels ({0} vs {1}) cannot be matched".
                             format(top_stripe.channel_count(), bottom_stripe.channel_count()))
        if top_stripe.version_count() != bottom_stripe.version_count():
            raise ValueError("Stripes with different number of versions ({0} vs {1}) cannot be matched".
                             format(top_stripe.version_count(), bottom_stripe.version_count()))

    @classmethod
    def extract_shift(cls, shifts):
        return tuple([int(round(sum(shifts[:, index]) / float(len(shifts)))) for index in [0, 1]])

    @classmethod
    def find_shift(cls, top_image, bottom_image):
        """
        Parameters
        ----------
        top_image: numpy.array
        bottom_image: numpy.array

        Returns
        -------
        [int, int]
            Height of overlay of two given images (number of common pixels on the bottom of top_image and top of
                bottom_image)
            Horizontal shift which needs to be applied to bottom image before matching
        """
        width = min(top_image.shape[1], bottom_image.shape[1])
        height = min(top_image.shape[0], bottom_image.shape[0]) // 2
        shift, _, _ = register_translation(top_image[-height:, :width], bottom_image[:height, :width], upsample_factor=8)
        return [height - shift[0], shift[1]]

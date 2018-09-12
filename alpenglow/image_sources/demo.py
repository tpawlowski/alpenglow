import numpy
import skimage
from skimage import data, dtype_limits

from alpenglow.image_sources.image_source import ImageSource


class DemoImageSource(ImageSource):
    """
    Implementation of image source generating source images from skimage.data.camera example.

    Versions are simulated with different blur levels. Each returning image is concatenated vertically from different
    channels. Different channel versions are implementing by applying various [0,1] -> [0,1] functions on pixel values,
    because example image skimage.data.camera has only one channel.
    """
    def __init__(self, stripe_count=1, version_count=1, channel_count=1, overlap=0.3, vertical_shifts=(0,)):
        """
        Parameters
        ----------
        stripe_count: int
            Number of stripes to which skimage.data.camera should be split
        version_count: int
            Number of differently blurred versions for each stripe.
        channel_count: int
            Number of channels generated for the image
        overlap: float
            Ratio representing part of the image common to two consecutive images. Value 0.4 notes that bottom 40% of
            the first source image in any version shows the same part of the example image as top 40% of the second
            image.
        vertical_shifts: tuple of int
            Number of additional pixels which will be concatenated on the left side of the image to simulate camera
            shifts. To Nth stripe vertical_strips[N%len(vertical_strips)] columns of pixels will be appended on the
            left. Columns on the right will be appended to equalize number of columns in each image.
        """
        super(DemoImageSource, self).__init__()
        self._stripe_count = stripe_count
        self._version_count = version_count
        self._channel_count = channel_count
        self.overlap = overlap
        self.vertical_shifts = vertical_shifts

        self.source_image = data.camera()
        self.stripe_height = int(self.source_image.shape[0] / (self._stripe_count * (1. - self.overlap) + self.overlap))
        self.overlap_height = int(self.stripe_height * self.overlap)

    def get_image(self, stripe_id, version_id):
        stripe_image_id = stripe_id % self.stripe_count()
        if (stripe_id // self.stripe_count()) % 2 == 1:
            stripe_image_id = self.stripe_count() - 1 - stripe_image_id

        blur_level = self.__get_blur_level(version_id)
        raw_stripe = self.__get_raw_stripe(stripe_image_id)
        shifted_stripe = self.__shift(self.__get_shift(stripe_image_id), raw_stripe)

        channels = [self.__class__.__prepare_channel_stripe(shifted_stripe, blur_level, channel_id) for channel_id in range(self.channel_count())]

        return ImageSource.loop_image(numpy.concatenate(channels, axis=1), stripe_id, self.stripe_count())

    def stripe_count(self):
        return self._stripe_count

    def version_count(self):
        return self._version_count

    def channel_count(self):
        return self._channel_count

    def __get_raw_stripe(self, stripe_id):
        row_from = (self.stripe_height - self.overlap_height) * stripe_id
        row_to = row_from + self.stripe_height if stripe_id < self.stripe_count() - 1 else self.source_image.shape[0]

        return self.source_image[row_from:row_to]

    def __shift(self, shift, stripe):
        parts = []
        if shift[0] > 0:
            parts.append(stripe[:, (shift[0] - 1)::-1])
        parts.append(stripe)
        if shift[1] > 0:
            parts.append(stripe[:, :(stripe.shape[1] - shift[1] - 1):-1])

        return numpy.concatenate(parts, axis=1)

    def __get_shift(self, stripe_id):
        left_shift = self.vertical_shifts[stripe_id % len(self.vertical_shifts)]
        right_shift = max(self.vertical_shifts) - left_shift
        return left_shift, right_shift

    def __get_blur_level(self, version):
        assert version < self.version_count()
        if self.version_count() == 1:
            return 0.
        return 2.0 * version / (self.version_count() - 1)

    @classmethod
    def __prepare_channel_stripe(cls, stripe, blur_level, channel):
        max = dtype_limits(stripe, clip_negative=False)[1]
        channel_map = cls.__channel_function(channel)
        pixel_map = numpy.vectorize(lambda x: int(round(channel_map(float(x) / max) * max)))
        mapped_stripe = pixel_map(stripe).astype(stripe.dtype)
        blurred_stripe = numpy.vectorize(lambda x: int(round(x * max)))(skimage.filters.gaussian(mapped_stripe, blur_level)).astype(stripe.dtype)
        return blurred_stripe

    @classmethod
    def __channel_function(cls, channel):
        """
        Selects demo function with which pixels of given channel should be mapped in order to
        simulate multichannel image.

        Parameters
        ----------
        channel: int
            Channel id for which function should be returned.
        Returns
        -------
        function [0,1] -> [0,1]
        """
        functions = [
            lambda x: x,
            lambda x: 1. - x,
            lambda x: x ** 2,
            lambda x: x + 0.5 if x <= 0.5 else x - 0.5
        ]
        return functions[channel % len(functions)]

from unittest import TestCase

import numpy
from numpy.testing import assert_array_equal, assert_array_almost_equal
from skimage.filters import gaussian
from skimage.util import invert

from alpenglow.image_sources.demo import DemoImageSource


class TestDemoImageSource(TestCase):
    """
    Test basic functionality of DemoImageSource
    """
    def test_sample_image(self):
        # given
        source = DemoImageSource(stripe_count=2, version_count=3)

        # when
        image = source.get_image(0, 0)

        # then
        self.assertEqual((301, 512), image.shape)

    def test_second_image_overlaps(self):
        # given
        source = DemoImageSource(2, 3)

        # when
        image = source.get_image(1, 0)

        # then
        shape = image.shape
        self.assertEqual((301, 512), shape)
        assert_array_equal(image, source.source_image[(512-shape[0]):, :])

    def test_first_channel(self):
        # given
        source = DemoImageSource(stripe_count=2, version_count=3, channel_count=2)

        # when
        image = source.get_image(0, 0)

        # then
        shape = image.shape

        assert_array_equal(image[:shape[0], :int(shape[1]/2)], source.source_image[0:shape[0], 0:int(shape[1]/2)])

    def test_second_channel_is_inverted(self):
        # given
        source = DemoImageSource(stripe_count=2, version_count=3, channel_count=2)

        # when
        image = source.get_image(0, 0)

        # then
        shape = image.shape

        assert_array_equal(image[:, int(shape[1] / 2):], invert(source.source_image[:shape[0], :int(shape[1] / 2)]))

    def test_versions_are_blurred(self):
        # given
        source = DemoImageSource(stripe_count=2, version_count=3, channel_count=2)

        # when
        image = source.get_image(0, 2)

        # then
        shape = image.shape

        assert_array_equal(image[:, :int(shape[1] / 2)],
                           numpy.vectorize(lambda x: int(round(x * 255)))(gaussian(source.source_image[:shape[0], :int(shape[1] / 2)], 2.0)).astype(image.dtype))

    def test_middle_version_blur(self):
        # given
        source = DemoImageSource(stripe_count=2, version_count=3, channel_count=2)

        # when
        image = source.get_image(0, 2)

        # then
        shape = image.shape

        assert_array_almost_equal(image[:shape[0], :int(shape[1] // 2)],
                                  numpy.vectorize(lambda x: int(round(x * 255)))(gaussian(source.source_image[:shape[0], :int(shape[1] // 2)], 2.0)).astype(image.dtype),
                                  decimal=0)

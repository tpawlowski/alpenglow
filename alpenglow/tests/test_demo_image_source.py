from unittest import TestCase

from numpy.testing import assert_array_equal, assert_almost_equal
from skimage.filters import gaussian
from skimage.util import invert

from alpenglow.demo_image_source import DemoImageSource


class TestDemoImageSource(TestCase):
    """
    Test basic functionality of DemoImageSource
    """
    def test_sample_image(self):
        # given
        source = DemoImageSource(2, 3)

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
        source = DemoImageSource(2, 3, channel_count=2)

        # when
        image = source.get_image(0, 0)

        # then
        shape = image.shape

        assert_array_equal(image[:int(shape[0]/2), :shape[1]], source.source_image[0:int(shape[0]/2), 0:shape[1]])

    def test_second_channel_is_inverted(self):
        # given
        source = DemoImageSource(2, 3, channel_count=2)

        # when
        image = source.get_image(0, 0)

        # then
        shape = image.shape

        assert_array_equal(image[int(shape[0] / 2):, :shape[1]], invert(source.source_image[0:int(shape[0] / 2), 0:shape[1]]))

    def test_versions_are_blurred(self):
        # given
        source = DemoImageSource(2, 3, channel_count=2)

        # when
        image = source.get_image(0, 2)

        # then
        shape = image.shape

        assert_array_equal(image[:int(shape[0] / 2), :shape[1]],
                           (gaussian(source.source_image[:int(shape[0] / 2), :shape[1]], 4.0) * 255).astype(image.dtype))

    def test_middle_version_blur(self):
        # given
        source = DemoImageSource(2, 3, channel_count=2)

        # when
        image = source.get_image(0, 1)

        # then
        shape = image.shape

        assert_array_equal(image[:int(shape[0] / 2), :shape[1]],
                           (gaussian(source.source_image[:int(shape[0] / 2), :shape[1]], 2.0) * 255).astype(image.dtype))

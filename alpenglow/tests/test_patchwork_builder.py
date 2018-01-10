from unittest import TestCase

from numpy.testing import assert_array_equal
from skimage import data

from alpenglow.demo_image_source import DemoImageSource
from alpenglow.old_matching_algorithm import OldMatchingAlgorithm
from alpenglow.patchwork_builder import PatchworkBuilder


class TestPatchworkBuilder(TestCase):
    def test_single_stripe(self):
        # given
        matching_algorithm = OldMatchingAlgorithm([0], [0])
        builder = PatchworkBuilder(matching_algorithm)
        image_source = DemoImageSource(stripe_count=3)
        stripe = image_source.get_stripe(0)

        # when
        builder.stitch(stripe)

        # then
        patchwork = builder.get()
        assert_array_equal(stripe.get_image(0), patchwork.get_image(0))

    def test_stitching_two_stripes(self):
        # given
        matching_algorithm = OldMatchingAlgorithm([0], [0])
        builder = PatchworkBuilder(matching_algorithm)
        image_source = DemoImageSource(stripe_count=2)

        # when
        builder.stitch(image_source.get_stripe(0))
        builder.stitch(image_source.get_stripe(1))

        # then
        patchwork = builder.get()
        assert_array_equal(image_source.source_image, patchwork.get_image(0))

    def test_stitching_two_stripes_with_shift(self):
        # given
        matching_algorithm = OldMatchingAlgorithm([0], [0])
        builder = PatchworkBuilder(matching_algorithm)
        image_source = DemoImageSource(stripe_count=2, vertical_shifts=(0, 20))

        # when
        builder.stitch(image_source.get_stripe(0))
        builder.stitch(image_source.get_stripe(1))

        # then
        patchwork = builder.get()
        assert_array_equal(image_source.source_image, patchwork.get_image(0)[:, :512])

    def test_stitching_two_stripes_with_channels(self):
        # given
        matching_algorithm = OldMatchingAlgorithm([0], [0])
        builder = PatchworkBuilder(matching_algorithm)
        image_source = DemoImageSource(stripe_count=2, channel_count=2)

        # when
        builder.stitch(image_source.get_stripe(0))
        builder.stitch(image_source.get_stripe(1))

        # then
        patchwork = builder.get()
        assert_array_equal(image_source.source_image, patchwork.get_channel_image(0, 0))

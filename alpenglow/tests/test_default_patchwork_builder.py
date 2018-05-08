from unittest import TestCase

import numpy
from numpy.testing import assert_array_equal, assert_array_almost_equal

from alpenglow.image_sources.demo import DemoImageSource
from alpenglow.matching_algorithms.old import OldMatchingAlgorithm
from alpenglow.patchwork_builders.default import PatchworkBuilder


class TestDefaultPatchworkBuilder(TestCase):
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
        assert_array_almost_equal(image_source.source_image, patchwork.get_image(0), decimal=0)

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
        assert_array_almost_equal(image_source.source_image, patchwork.get_image(0)[:, :512], decimal=0)

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
        assert_array_almost_equal(image_source.source_image, numpy.array(patchwork.get_channel_image(0, 0)), decimal=0)

    def test_benchmarks_are_collected(self):
        # given
        matching_algorithm = OldMatchingAlgorithm([0], [0])
        builder = PatchworkBuilder(matching_algorithm)
        image_source = DemoImageSource(stripe_count=2, vertical_shifts=(0, 20))

        # when
        builder.stitch(image_source.get_stripe(0))
        builder.stitch(image_source.get_stripe(1))

        # then
        patchwork = builder.get()
        stitching_times, result_generation_time = builder.benchmark()
        self.assertEqual(2, len(stitching_times))
        self.assertIsNotNone(result_generation_time)
        self.assertGreater(result_generation_time, 0.0)

    def test_gradient_merge_arrays(self):
        # given
        image_one = numpy.array([[1, 2], [3, 4], [5, 6], [7, 8]])
        image_two = numpy.array([[10, 1], [9, 2], [8, 3], [7, 4]])

        # when
        image = PatchworkBuilder.gradient_merge_arrays(image_one, image_two)

        # then
        assert_array_equal(image_one[0] * 0.8 + image_two[0] * 0.2, image[0])
        assert_array_equal(image_one[1] * 0.6 + image_two[1] * 0.4, image[1])
        assert_array_equal([[2.8,  1.8], [5.4,  3.2], [6.8,  4.2], [7.,  4.8]], image)

from unittest import TestCase

from numpy.testing import assert_array_almost_equal

from alpenglow.image_sources.demo import DemoImageSource
from alpenglow.matching_algorithms.old import OldMatchingAlgorithm
from alpenglow.patchwork_builders.lazy import LazyPatchworkBuilder


class TestLazyPatchworkBuilder(TestCase):
    def test_stitching_two_stripes(self):
        # given
        matching_algorithm = OldMatchingAlgorithm([0, 1], [0])
        builder = LazyPatchworkBuilder(matching_algorithm)
        image_source = DemoImageSource(stripe_count=2, version_count=3)

        # when
        builder.stitch(image_source.get_stripe(0))
        builder.stitch(image_source.get_stripe(1))

        # then
        patchwork = builder.get()
        assert_array_almost_equal(image_source.source_image, patchwork[:][0], decimal=0)

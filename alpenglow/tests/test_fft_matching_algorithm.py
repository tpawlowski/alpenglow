from unittest import TestCase

from numpy.testing import assert_equal

from alpenglow.image_sources.demo import DemoImageSource
from alpenglow.matching_algorithms.fft import FftMatchingAlgorithm


class TestFftMatchingAlgorithm(TestCase):
    def test_match(self):
        # given
        image_source = DemoImageSource(3, 3, channel_count=3, overlap=0.4, vertical_shifts=(19, 38, 0))
        algorithm = FftMatchingAlgorithm([0, 2], [0, 1])

        top_stripe = image_source.get_stripe(0)
        bottom_stripe = image_source.get_stripe(1)

        # when
        shift = algorithm.match(top_stripe, bottom_stripe)

        # then
        assert_equal([92, -19], shift)




from unittest import TestCase

import numpy
from numpy.testing import assert_array_almost_equal, assert_equal

from alpenglow.image_sources.demo import DemoImageSource
from alpenglow.matching_algorithms.old import OldMatchingAlgorithm


class TestOldMatchingAlgorithm(TestCase):
    def test_finding_shift(self):
        # given
        image_source = DemoImageSource(3, 1, overlap=0.4, vertical_shifts=(19, 38, 0))
        top_image = image_source.get_image(0, 0)
        bottom_image = image_source.get_image(1, 0)

        # when
        shift = OldMatchingAlgorithm.find_shift(top_image, bottom_image)

        # then
        assert_array_almost_equal(shift, [92., -19.], decimal=0)

    def test_multiple_channels(self):
        # given
        image_source = DemoImageSource(3, 3, channel_count=3, overlap=0.4, vertical_shifts=(19, 38, 0))
        algorithm = OldMatchingAlgorithm([0, 2], [0, 1])

        top_stripe = image_source.get_stripe(0)
        bottom_stripe = image_source.get_stripe(1)

        # when
        shifts = algorithm.measure_shifts(top_stripe, bottom_stripe)

        # then
        assert_array_almost_equal(shifts, [[93., -19.]] * 4, decimal=0)

    def test_extract_shift(self):
        # given
        measured_shifts = numpy.array([[77.875, 20.75], [77.875, 20.75], [78.125, 20.25]], numpy.float)

        # when
        shift = OldMatchingAlgorithm.extract_shift(measured_shifts)

        # then
        assert_equal(shift, (78, 21))

    def test_validate_shift(self):
        # given
        measured_shifts = numpy.array([[77.875, 20.75], [77.875, 20.75], [78.125, 20.25]], numpy.float)
        shift = (78, 21)

        # when & then
        OldMatchingAlgorithm.validate_shift(shift, measured_shifts)



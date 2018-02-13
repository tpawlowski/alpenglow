from unittest import TestCase

from alpenglow.benchmarking_image_source import BenchmarkingImageSource
from alpenglow.demo_image_source import DemoImageSource


class TestBenchmarkingImageSource(TestCase):
    """
    Test basic functionality of DemoImageSource
    """
    def test_inner_source_is_used(self):
        # given
        inner_source = DemoImageSource(stripe_count=2, version_count=3)
        source = BenchmarkingImageSource(inner_source)

        # when
        image = source.get_image(0, 0)

        # then
        self.assertEqual(inner_source.get_image(0, 0).shape, image.shape)
        self.assertGreater(source.total_fetching_time(), 0.0)

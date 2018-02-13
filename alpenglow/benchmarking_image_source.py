from time import time

from alpenglow.image_source import ImageSource


class BenchmarkingImageSource(ImageSource):
    """
    Implementation of image source fetching images from local file system.
    """
    def __init__(self, image_source):
        self.image_source = image_source
        self.fetch_times = []

    def get_image(self, stripe_id, version_id):
        start_time = time()
        image = self.image_source.get_image(stripe_id, version_id)
        self.fetch_times.append([time() - start_time, stripe_id, version_id])
        return image

    def stripe_count(self):
        return self.image_source.stripe_count()

    def version_count(self):
        return self.image_source.version_count()

    def channel_count(self):
        return self.image_source.channel_count()

    def total_fetching_time(self):
        return sum([x[0] for x in self.fetch_times])

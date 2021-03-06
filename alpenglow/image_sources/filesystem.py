from alpenglow.image_sources.image_source import ImageSource
import skimage.external.tifffile as tiff


class FilesystemImageSource(ImageSource):
    """
    Implementation of image source fetching images from local file system.
    """
    def __init__(self, path_format, stripe_ids, version_ids, channel_count=1):
        self.path_format = path_format
        self.stripe_ids = stripe_ids
        self.version_ids = version_ids
        self._channel_count = channel_count

    def get_image(self, stripe_id, version_id):
        stripe_image_id = stripe_id % len(self.stripe_ids)
        if (stripe_id // len(self.stripe_ids)) % 2 == 1:
            stripe_image_id = len(self.stripe_ids) - 1 - stripe_image_id

        path = self.path_format.format(stripe_id=self.stripe_ids[stripe_image_id], version_id=self.version_ids[version_id])
        return ImageSource.loop_image(tiff.TiffFile(path).asarray().swapaxes(0, 1), stripe_id, len(self.stripe_ids))

    def stripe_count(self):
        return len(self.stripe_ids)

    def version_count(self):
        return len(self.version_ids)

    def channel_count(self):
        return self._channel_count

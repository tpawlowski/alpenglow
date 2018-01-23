import cottoncandy
from io import BytesIO

from alpenglow.image_source import ImageSource
import skimage.external.tifffile as tiff


class S3ImageSource(ImageSource):
    """
    Implementation of image source fetching images from s3 storage.
    """
    def __init__(self, path_format, stripe_ids, version_ids, key, secret, bucket, endpoint, channel_count=1, mapping=None):
        self.path_format = path_format
        self.stripe_ids = stripe_ids
        self.version_ids = version_ids
        self._channel_count = channel_count
        self.connection = cottoncandy.get_interface(bucket, ACCESS_KEY=key, SECRET_KEY=secret, endpoint_url=endpoint, verbose=False)
        self.mapping = mapping

    def get_image(self, stripe_id, version_id):
        external_stripe_id = self.stripe_ids[stripe_id]
        external_version_id = self.version_ids[version_id]

        if self.mapping is not None:
            external_stripe_id, external_version_id = self.mapping(external_stripe_id, external_version_id)

        path = self.path_format.format(stripe_id=external_stripe_id, version_id=external_version_id)
        return tiff.TiffFile(BytesIO(self.connection.download_object(path))).asarray().swapaxes(0, 1)

    def stripe_count(self):
        return len(self.stripe_ids)

    def version_count(self):
        return len(self.version_ids)

    def channel_count(self):
        return self._channel_count

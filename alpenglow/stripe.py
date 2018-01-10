from abc import ABCMeta, abstractmethod


class Stripe:
    """
    Stripe representing a single horizontal strip of an image.
    """
    __metaclass__ = ABCMeta

    def __init__(self):
        self.cached_shape = None
        self.cached_dtype = None

    @abstractmethod
    def get_image(self, version_id):
        """
        Parameters
        ----------
        version_id: int
            version of the fetched image starting from 0.

        Returns
        -------
        ndarray
            NumPy array of shape (height, width) containing floats representing pixel values
        """
        pass

    @abstractmethod
    def version_count(self):
        """
        Number of versions of images in the stripe
        """
        pass

    @abstractmethod
    def channel_count(self):
        """
        Number of channels in each image
        """
        pass

    def get_dtype(self):
        """
        Returns dtype of images (same in each version)
        """
        if self.cached_dtype is None:
            self.cached_dtype = self.get_image(0).dtype
        return self.cached_dtype

    def get_shape(self):
        """
        Returns
        -------
        shape: tuple(int, int)
            height, width of images (same in each version)
        """
        if self.cached_shape is None:
            self.cached_shape = self.get_image(0).shape
        return self.cached_shape

    def get_channel_image(self, version_id, channel_id):
        """
        Parameters
        ----------
        version_id: int
            version of the fetched image starting from 0.
        channel_id: int
            id of the channel extracted from the image

        Returns
        -------
        ndarray
            NumPy array of shape (height / channel_count, width) containing floats representing pixel values
        """
        image = self.get_image(version_id)
        channel_height = image.shape[0] // self.channel_count()
        return image[(channel_id * channel_height):((channel_id + 1) * channel_height), :]

    def get_channel_shape(self):
        """

        Returns
        -------
        shape: tuple(int, int)
            height, width of single channel image (same in each version and channel)
        """
        return self.get_shape()[0] // self.channel_count(), self.get_shape()[1]

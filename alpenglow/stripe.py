from abc import ABCMeta, abstractmethod
from concurrent.futures import Future


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
            image = self.get_image(0)
            self.cached_shape = image.shape
            self.cached_dtype = image.dtype
        return self.cached_dtype

    def get_shape(self):
        """
        Returns
        -------
        shape: tuple(int, int)
            height, width of images (same in each version)
        """
        if self.cached_shape is None:
            image = self.get_image(0)
            self.cached_shape = image.shape
            self.cached_dtype = image.dtype
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

    def get_image_future(self, version_id):
        """
        Parameters
        ----------
        version_id: int
            version of the fetched image starting from 0.

        Returns
        -------
        ndarray: Future
            Future for NumPy array of shape (height, width) containing floats representing pixel values.
        """
        future = Future()
        future.set_result(self.get_image(version_id))
        return future

    def get_channel_image_future(self, version_id, channel_id):
        """

        Parameters
        ----------
        version_id: int
            version of the fetched image starting from 0.
        channel_id: int
            id of the channel extracted from the image

        Returns
        -------
        ndarray: Future
            Future for NumPy array of shape (height / channel_count, width) containing floats representing pixel values
        """
        future = Future()
        channel_count = self.channel_count()
        self.get_image_future(version_id).add_done_callback(
            lambda image: future.set_result(image.result()[(channel_id * (image.result().shape[0] // channel_count)):((channel_id + 1) * (image.result().shape[0] // channel_count)), :]))
        return future

    def get_channel_shape(self):
        """

        Returns
        -------
        shape: tuple(int, int)
            height, width of single channel image (same in each version and channel)
        """
        return self.get_shape()[0] // self.channel_count(), self.get_shape()[1]

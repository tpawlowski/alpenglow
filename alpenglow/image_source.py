from abc import ABCMeta, abstractmethod
from numpy import ndarray

from alpenglow.lazy_stripe import LazyStripe


class ImageSource:
    """
    Interface for image source enabling to fetch images by stripes.
    """
    __metaclass__ = ABCMeta

    def get_stripe(self, stripe_id):
        """
        Parameters
        ----------
        stripe_id: int

        Returns
        -------
        Stripe with given id
        """
        return LazyStripe(stripe_id, self)

    @abstractmethod
    def get_image(self, stripe_id, version_id):
        """
        Fetches or generates NumPy array with pixel values for given stripe and version of represented image.

        Parameters
        ----------
        stripe_id : int
            stripe id starting from 0
        version_id : int
            version id starting from 0

        Returns
        -------
        ndarray
            NumPy array of shape (height, width) containing floats representing pixel values
        """
        pass

    @abstractmethod
    def stripe_count(self):
        """

        Returns
        -------
        int
            Number of stripes available in represented image.
        """
        pass

    @abstractmethod
    def version_count(self):
        """

        Returns
        -------
        int
            Number of versions of each stripe.
        """
        pass

    @abstractmethod
    def channel_count(self):
        """

        Returns
        -------
        int
            Number of channels in each source image
        """
        pass

from abc import ABCMeta, abstractmethod


class MatchingAlgorithm:
    """
    Interface for class finding shift between two images.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def match(self, top_stripe, bottom_stripe):
        """
        Matches shift of two images and returns vertical and horizontal shift which should be applied to the bottom
        image in order to stitch it to the top image

        Parameters
        ----------
        top_stripe: Stripe
            Stripe to which bottom part is appended.
        bottom_stripe: Stripe
            Stripe appended to the top one.

        Returns
        -------
        tuple(int, int)
            number of detected common rows on the bottom of top_stripe and top of bottom stripe and horizontal shift
            which needs to be applied to the bottom stripe before stitching.
        """
        pass


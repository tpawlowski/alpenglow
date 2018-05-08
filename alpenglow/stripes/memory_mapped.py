from alpenglow.stripes.stripe import Stripe


class MemoryMappedStripe(Stripe):
    """
    Stripe keeping its data in a memory mapped numpy.array.

    Notes
    -----
    Memory mapped stripe can be mutated using append method.
    """

    def __init__(self, data, channel_count):
        """
        Creates memory mapped stripe from given stripe

        Parameters
        ----------
        stripe: Stripe
        """
        super(MemoryMappedStripe, self).__init__()
        self._channel_count = channel_count
        self._data = data

    def get_image(self, version_id):
        """
        Returns
        -------
        numpy.array
            Array representing given version
        """
        return self._data[version_id]

    def version_count(self):
        return self._data.shape[0]

    def channel_count(self):
        return self._channel_count

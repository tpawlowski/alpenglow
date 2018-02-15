from alpenglow.stripe import Stripe


class LazyStripe(Stripe):
    """
    Stripe fetches images from an underlying image source.
    """

    def __init__(self, stripe_id, image_source):
        """
        Parameters
        ----------
        stripe_id: int
            Id of the stripe
        image_source: ImageSource
            Source from which parts are fetched.
        """
        super(LazyStripe, self).__init__()
        self.stripe_id = stripe_id
        self.image_source = image_source
        self.cached_image = None
        self.cached_image_future = None

    def get_image(self, version_id):
        """
        Fetches image from image_source and caches it by version_id keeping only 1 last value.
        """
        if self.cached_image is None or self.cached_image[0] != version_id:
            self.cached_image = [version_id, self.image_source.get_image(self.stripe_id, version_id)]
        return self.cached_image[1]

    def get_image_future(self, version_id):
        """
        Fetches image from image_source and caches it by version_id keeping only 1 last value.
        """
        if self.cached_image_future is None or self.cached_image_future[0] != version_id:
            self.cached_image_future = [version_id, self.image_source.get_image_future(self.stripe_id, version_id)]
        return self.cached_image_future[1]

    def version_count(self):
        return self.image_source.version_count()

    def channel_count(self):
        return self.image_source.channel_count()

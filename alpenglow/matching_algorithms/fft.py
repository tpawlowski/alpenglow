import concurrent

import numpy

from alpenglow.matching_algorithms.matching_algorithm import MatchingAlgorithm


class FftMatchingAlgorithm(MatchingAlgorithm):
    """
    Implementation of stripe matching algorithm derived from file stitching2.py
    """
    def __init__(self, versions, channels):
        """
        Parameters
        ----------
        versions: [int]
            List of versions to test for shift
        channels: [int]
            List of channels to test for shift
        """
        if not versions:
            raise ValueError("Shift must be detected in at least one version of images")
        self._versions = versions

        if not channels:
            raise ValueError("Shift must be detected in at least one channel")
        self._channels = channels

    def match(self, top_stripe, bottom_stripe):
        top_shape = top_stripe.get_channel_shape()
        bottom_shape = bottom_stripe.get_channel_shape()

        width = min(top_shape[1], bottom_shape[1])
        height = min(top_shape[0], bottom_shape[0]) // 2
        shape = (height, width)

        futures = {}
        for version_id in self._versions:
            for channel_id in self._channels:
                futures[top_stripe.get_channel_image_future(version_id, channel_id)] = ('top', version_id, channel_id)
                futures[bottom_stripe.get_channel_image_future(version_id, channel_id)] = ('bottom', version_id, channel_id)

        correlation = numpy.zeros(shape, dtype=numpy.complex128)

        completed = {}
        for future in concurrent.futures.as_completed(futures):
            position = futures[future]
            pair_key = (position[1], position[2])
            try:
                if position[0] == 'top':
                    top_image, bottom_image = future.result(), completed[pair_key]
                else:
                    top_image, bottom_image = completed[pair_key], future.result()
                del completed[pair_key]
                correlation += FftMatchingAlgorithm.cross_correlation(top_image[-height:, :width], bottom_image[:height, :width])
            except KeyError:
                completed[pair_key] = future.result()

        midpoints = numpy.array([numpy.fix(axis_size / 2) for axis_size in shape])
        maxima = numpy.unravel_index(numpy.argmax(numpy.abs(correlation)), correlation.shape)
        shifts = numpy.array(maxima, dtype=numpy.int)

        shifts[shifts > midpoints] -= numpy.array(shape)[shifts > midpoints]
        shifts[0] = height - shifts[0]

        return shifts

    @classmethod
    def cross_correlation(cls, top_image, bottom_image):
        src_image = numpy.array(top_image, dtype=numpy.complex128, copy=False)
        target_image = numpy.array(bottom_image, dtype=numpy.complex128, copy=False)
        src_freq = numpy.fft.fftn(src_image)
        target_freq = numpy.fft.fftn(target_image)

        image_product = src_freq * target_freq.conj()

        return numpy.fft.ifftn(image_product)

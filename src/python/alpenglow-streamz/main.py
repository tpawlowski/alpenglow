import dask
import numpy
from streamz import Stream

from alpenglow.image_sources.demo import DemoImageSource
from alpenglow.matching_algorithms.fft import FftMatchingAlgorithm
from dask.distributed import Client


def sampling_function(version, version_count, sample_size):
    if sample_size == 1:  # accept middle one
        return version == version_count // 2
    elif sample_size == 2:  # accept edges
        return version == 0 or version == version_count - 1
    else:  # accept evenly distributed versions
        return (version == 0) or \
               (((version + 1) * (sample_size - 1)) % version_count) == 0 or \
               (version + 1) * (sample_size - 1) // version_count > version * (sample_size - 1) // version_count


def cross_correlation(version, stripe, top_image, bottom_image):
    width = min(top_image.shape[1], bottom_image.shape[1])
    height = min(top_image.shape[0], bottom_image.shape[0]) // 2
    correlation = FftMatchingAlgorithm.cross_correlation(top_image[-height:, :width], bottom_image[:height, :width])
    return (version, stripe, correlation, top_image.shape, bottom_image.shape)


def joinConsecutiveStripes(state, image_with_metadata):
    version, stripe, image = image_with_metadata
    tops, bottoms, first_stripe = state
    ready = []

    if first_stripe is None:
        first_stripe = stripe

    if stripe > first_stripe:
        top_id = (version, stripe - 1)
        if top_id in tops:
            top_image = tops[top_id]
            del tops[top_id]
            ready.append(cross_correlation(version, stripe - 1, top_image, image))
        else:
            bottoms[(version, stripe)] = image

    bottom_id = (version, stripe + 1)
    if bottom_id in bottoms:
        bottom_image = bottoms[bottom_id]
        del bottoms[bottom_id]
        ready.append(cross_correlation(version, stripe, image, bottom_image))
    else:
        tops[(version, stripe)] = image

    return (tops, bottoms, first_stripe), ready


def shifts(sums, correlation_with_metadata, sample_size=None):
    (version, stripe, correlation, top_shape, bottom_shape) = correlation_with_metadata

    if stripe not in sums:
        sums[stripe] = (correlation, 1)
    else:
        old_correlation, cnt = sums[stripe]
        sums[stripe] = (correlation + old_correlation, cnt + 1)

    if sums[stripe][1] == sample_size:
        correlation = sums[stripe][0]
        del sums[stripe]

        midpoints = numpy.array([numpy.fix(axis_size / 2) for axis_size in correlation.shape])
        maxima = numpy.unravel_index(numpy.argmax(numpy.abs(correlation)), correlation.shape)
        shifts = numpy.array(maxima, dtype=numpy.int)

        shifts[shifts > midpoints] -= numpy.array(correlation.shape)[shifts > midpoints]
        shifts[0] = correlation.shape[0] - shifts[0]

        return sums, [[stripe, list(shifts), top_shape]]

    return sums, []


if __name__ == '__main__':
    VERSION_COUNT = 5
    STRIPE_COUNT = 7
    N = 3
    MARGIN = 10

    image_source = DemoImageSource(
        stripe_count=STRIPE_COUNT,
        version_count=VERSION_COUNT,
        channel_count=1,
        vertical_shifts=(19, 38, 0),
        overlap=0.4,
    )

    client = Client(processes=False)

    source = Stream()
    source.filter(lambda x: sampling_function(x[0], VERSION_COUNT, N)).scatter()\
        .map(lambda x: (x[0], x[1], image_source.get_image(x[1], x[0]))).buffer(5)\
        .accumulate(joinConsecutiveStripes, returns_state=True, start=({}, {}, None)).flatten()\
        .accumulate(shifts, returns_state=True, start={}, sample_size=N).flatten() \
        .gather().sink(print)

    for stripe in range(STRIPE_COUNT):
        for version in range(VERSION_COUNT):
            source.emit([version, stripe])

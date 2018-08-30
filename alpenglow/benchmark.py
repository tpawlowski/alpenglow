import numpy

from alpenglow.image_sources.demo import DemoImageSource
from alpenglow.matching_algorithms.fft import FftMatchingAlgorithm
from alpenglow.patchwork_builders.default import PatchworkBuilder


class BenchmarkConfig:
    """
    Configuration of how demo images should be generated (if they are generated).
    """
    def __init__(self,
                 stripe_count=7,
                 version_count=5,
                 channel_count=1,
                 stripe_shifts=(19, 38, 0),
                 stripe_overlap=0.4,
                 sample_size=3,
                 margin=30,
                 verbosity=0):
        self.stripe_count = stripe_count
        self.version_count = version_count
        self.channel_count = channel_count
        self.stripe_shifts = stripe_shifts
        self.stripe_overlap = stripe_overlap
        self.sample_size = sample_size
        self.margin = margin
        self.verbosity = verbosity

    def to_dict(self):
        return dict(
            stripe_count=self.stripe_count,
            version_count=self.version_count,
            channel_count=self.channel_count,
            stripe_shift=self.stripe_shifts,
            stripe_overlap=self.stripe_overlap,
            sample_size=self.sample_size,
            margin=self.margin,
            verbosity=self.verbosity
        )

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

def get_image_order(config):
    """

    Parameters
    ----------
    config: BenchmarkConfig

    Returns
    -------
    Iterator for pairs (stripe, version) occuring in order they usually appear in the stream

    """
    return ((stripe, version) for stripe in range(config.stripe_count) for version in range(config.version_count))


def get_image_source(config):
    """

    Parameters
    ----------
    config: BenchmarkConfig

    Returns
    -------
    ImageSource object capable of generating image based on stripe and version.

    """
    return DemoImageSource(
        stripe_count=config.stripe_count,
        version_count=config.version_count,
        channel_count=config.channel_count,
        vertical_shifts=config.stripe_shifts,
        overlap=config.stripe_overlap
    )


def is_in_sample(config, version):
    if config.sample_size == 1:  # accept middle one
        return version == config.version_count // 2
    elif config.sample_size == 2:  # accept edges
        return version == 0 or version == config.version_count - 1
    else:  # accept evenly distributed versions
        return (version == 0) or \
               (((version + 1) * (config.sample_size - 1)) % config.version_count) == 0 or \
               (version + 1) * (config.sample_size - 1) // config.version_count > version * (
               config.sample_size - 1) // config.version_count


class CorrelationState:
    def __init__(self, config):
        self.first_stripe = 0
        self.bottoms = {}
        self.tops = {}
        print("create state")

    def apply(self, version, stripe, image):
        ready_correlations = []

        if stripe > self.first_stripe:
            top_id = (version, stripe - 1)
            if top_id in self.tops:
                top_image = self.tops[top_id]
                del self.tops[top_id]
                correlation = self.__correlation(top_image, image)
                ready_correlations.append([stripe - 1, correlation, top_image.shape])
            else:
                self.bottoms[(version, stripe)] = image

        bottom_id = (version, stripe + 1)
        if bottom_id in self.bottoms:
            bottom_image = self.bottoms[bottom_id]
            del self.bottoms[bottom_id]
            correlation = self.__correlation(image, bottom_image)
            ready_correlations.append([stripe, correlation, image.shape])
        else:
            self.tops[(version, stripe)] = image

        return ready_correlations

    def __correlation(self, top_image, bottom_image):
        width = min(top_image.shape[1], bottom_image.shape[1])
        height = min(top_image.shape[0], bottom_image.shape[0]) // 2

        return FftMatchingAlgorithm.cross_correlation(top_image[-height:, :width], bottom_image[:height, :width])


class ShiftState:
    def __init__(self, config):
        self.sample_size = config.sample_size
        self.sums = {}

    def apply(self, stripe, correlation, top_shape):
        if stripe not in self.sums:
            self.sums[stripe] = (correlation, 1)
        else:
            old_correlation, cnt = self.sums[stripe]
            self.sums[stripe] = (correlation + old_correlation, cnt + 1)

        if self.sums[stripe][1] == self.sample_size:
            correlation = self.sums[stripe][0]
            del self.sums[stripe]
            return self.__extract_shift(stripe, correlation, top_shape)

        return None

    def __extract_shift(self, stripe, correlation, shape):
        midpoints = numpy.array([numpy.fix(axis_size / 2) for axis_size in correlation.shape])
        maxima = numpy.unravel_index(numpy.argmax(numpy.abs(correlation)), correlation.shape)
        shifts = numpy.array(maxima, dtype=numpy.int)

        shifts[shifts > midpoints] -= numpy.array(correlation.shape)[shifts > midpoints]
        shifts[0] = correlation.shape[0] - shifts[0]

        return [stripe, list(shifts), shape]


class PositionState:
    def __init__(self, config):
        self.config = config
        self.margin = config.margin

        self.waiting = {}
        self.current = 0
        self.width = None
        self.x = config.margin
        self.y = 0
        self.previous_overlay = 0

    def apply(self, stripe, shift, shape):
        positions = []
        if self.width is None:
            self.width = 2 * self.margin + shape[1]

        if stripe >= self.current:
            self.waiting[stripe] = (shift, shape)

        while self.current in self.waiting:
            (shift, shape) = self.waiting[self.current]
            del self.waiting[self.current]
            positions.append([self.current, self.x, self.y, self.width, self.previous_overlay, shift[0], shift[1]])
            self.x += shift[1]
            self.y += shape[0] - shift[0]
            self.previous_overlay = shift[0]
            self.current += 1

        return positions


class DelayDownloadState:
    def __init__(self, config):
        self.config = config
        self.metadata = set()
        self.image_ids = set()

    def apply_image_id(self, stripe, version):
        if is_in_sample(self.config, version):
            return False
        elif (stripe, version) in self.metadata:
            self.metadata.remove((stripe, version))
            return True
        else:
            self.image_ids.add((stripe, version))
            return False

    def apply_metadata(self, stripe, version):
        if is_in_sample(self.config, version):
            return False
        elif (stripe, version) in self.image_ids:
            self.image_ids.remove((stripe, version))
            return True
        else:
            self.metadata.add((stripe, version))
            return False


class MergeImageState:
    def __init__(self, config):
        self.config = config
        self.image_buffer = {}
        self.metadata_buffer = {}
        self.current = {}

    def apply_image(self, version, stripe, image):
        if version not in self.image_buffer:
            self.image_buffer[version] = {}

        if version not in self.metadata_buffer:
            self.metadata_buffer[version] = {}
            self.current[version] = (0, False)

        self.image_buffer[version][stripe] = image

        return self.__to_emit(version)

    def apply_metadata(self, tup):
        version = tup[0]
        stripe = tup[1]

        if version not in self.metadata_buffer:
            self.metadata_buffer[version] = {}
            self.current[version] = (0, False)
        if version not in self.image_buffer:
            self.image_buffer[version] = {}

        self.metadata_buffer[version][stripe] = tup[2:]

        return self.__to_emit(version)

    def __to_emit(self, version):
        results = []
        while True:
            (current_stripe, top_printed) = self.current[version]

            if top_printed:
                if current_stripe in self.metadata_buffer[version]\
                        and current_stripe in self.image_buffer[version]\
                        and (current_stripe + 1) in self.image_buffer[version]:
                    results.append(self.__overlay(version,
                                      self.metadata_buffer[version][current_stripe],
                                      self.image_buffer[version][current_stripe],
                                      self.image_buffer[version][current_stripe + 1]))
                    del self.metadata_buffer[version][current_stripe]
                    del self.image_buffer[version][current_stripe]
                    self.current[version] = (current_stripe + 1, False)
                else:
                    break
            else:
                if current_stripe in self.metadata_buffer[version]\
                        and current_stripe in self.image_buffer[version]:
                    results.append(self.__uniq(version,
                                   self.metadata_buffer[version][current_stripe],
                                   self.image_buffer[version][current_stripe]))
                    self.current[version] = (current_stripe, True)
                else:
                    break

        return results

    def __uniq(self, version, metadata, image):
        (x, y, width, top_overlay, bottom_overlay, _) = metadata
        height = image.shape[0] - top_overlay - bottom_overlay
        data = numpy.zeros((height, width), dtype=image.dtype)
        data[:, max(x, 0):min(x + image.shape[1], width)] = image[top_overlay:-bottom_overlay, max(-x, 0):min(image.shape[1], width - x)]

        return [version, data, y + top_overlay]

    def __overlay(self, version, metadata, top_image, bottom_image):
        (x, y, width, _, overlay, shift) = metadata
        height = overlay
        data = numpy.zeros((height, width), dtype=top_image.dtype)

        data[:, max(x, 0):min(x + top_image.shape[1], width)] = top_image[-overlay:, max(-x, 0):min(top_image.shape[1], width - x)]
        bottom_x = x + shift
        data[:, max(bottom_x, 0):min(bottom_x + bottom_image.shape[1], width)] =\
            PatchworkBuilder.gradient_merge_arrays(
                data[:, max(bottom_x, 0):min(bottom_x + bottom_image.shape[1], width)],
                bottom_image[:overlay, max(-bottom_x, 0):min(bottom_image.shape[1], width - bottom_x)])

        return [version, data, y + top_image.shape[0] - overlay]

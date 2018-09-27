import time

import concurrent

from alpenglow.benchmark import BenchmarkConfig, get_image_order, is_in_sample, get_image_source, CorrelationState, \
    ShiftState, PositionState, DelayDownloadState, MergeImageState, WindowState, validate, segmentation


REFERENCE_TIME = int(time.time() * 1000)
DEBUG_LEVEL = 2


def log(level, message):
    if level <= DEBUG_LEVEL:
        print("{}: {}".format(str(float(int(time.time() * 1000) - REFERENCE_TIME)/1000).rjust(6, ' '), message))


class AlpenglowRunner:
    """
    Implementation using inside knowledge to run elements in best order. Single process, multi threaded.
    """
    def __init__(self, config):
        self.config = config
        self.image_source = get_image_source(config)

        self.delay_download_state = DelayDownloadState(config)

        self.correlation_state = CorrelationState(config)
        self.shift_state = ShiftState(config)
        self.positions_state = PositionState(config)
        self.merge_state = MergeImageState(config)
        self.window_state = WindowState(config)

        self.current_stripe = 0
        self.samples_to = -1
        self.rest_to = -1
        self.sample_futures = {}
        self.rest_futures = {}

    def apply(self, image_id):
        stripe, version = image_id

        if stripe > self.current_stripe + 1:
            self.__wait_for_images()

        if is_in_sample(self.config, image_id[1]):
            if stripe not in self.sample_futures:
                self.sample_futures[stripe] = {}
            self.sample_futures[stripe][self.image_source.get_image_future(stripe, version)] = version

        elif self.delay_download_state.apply_image_id(stripe, version):
            if stripe not in self.rest_futures:
                self.rest_futures[stripe] = {}
            self.rest_futures[stripe][self.image_source.get_image_future(stripe, version)] = version

    def __wait_for_images(self):
        self.__wait_for_samples(self.current_stripe)
        self.__wait_for_samples(self.current_stripe + 1)
        self.__wait_for_rest(self.current_stripe)
        self.current_stripe += 1

    def __wait_for_samples(self, sample_stripe):
        log(2, "waiting for samples {}".format(sample_stripe))
        if self.samples_to >= sample_stripe:
            return

        future_images = self.sample_futures[sample_stripe]
        del self.sample_futures[sample_stripe]
        for future_image in concurrent.futures.as_completed(future_images):
            version = future_images[future_image]
            image = future_image.result()
            log(3, "sample fetched {}".format((sample_stripe, version)))
            self.__apply_image(version, sample_stripe, image)

            for stripe, correlation, image_shape in self.correlation_state.apply(version, sample_stripe, image):
                shift = self.shift_state.apply(stripe, correlation, image_shape)
                if shift is not None:
                    log(3, "correlation calculated {}".format(stripe))
                    for position in self.positions_state.apply(*shift):
                        log(2, 'calculated position {}'.format(position))
                        for version in range(self.image_source.version_count()):
                            stripe = position[0]
                            if self.delay_download_state.apply_metadata(stripe, version):
                                if stripe not in self.rest_futures:
                                    self.rest_futures[stripe] = {}
                                self.rest_futures[stripe][self.image_source.get_image_future(stripe, version)] = version

                            for merged_image in self.merge_state.apply_metadata([version] + position):
                                self.__apply_merged_image(merged_image)

        self.samples_to = sample_stripe

    def __wait_for_rest(self, stripe):
        log(2, "waiting for rest {}".format(stripe))
        if self.rest_to >= stripe:
            return
        future_images = self.rest_futures[stripe]
        del self.rest_futures[stripe]
        for future_image in concurrent.futures.as_completed(future_images):
            version = future_images[future_image]
            image = future_image.result()
            self.__apply_image(version, stripe, image)
        self.rest_to = stripe

    def __apply_image(self, version, stripe, image):
        log(3, "merging {}".format((stripe, version)))
        for merged_image in self.merge_state.apply_image(version, stripe, image):
            self.__apply_merged_image(merged_image)

    def __apply_merged_image(self, merged_image):
        for from_y, to_y, image_3d in self.window_state.apply(*merged_image):
            log(1, "[{},{}): {}".format(from_y, to_y, validate(segmentation(image_3d))))


if __name__ == '__main__':
    log(0, 'start')
    config = BenchmarkConfig.from_dict(dict(verbosity=1,
                                 replication_factor=7,
                                 sample_size=25,
                                 window_length=256,
                                 window_step=128,
                                 image_source="filesystem",
                                 image_source_threads=4,
                                 image_source_config=dict(
                                     args=['/Users/tpawlowski/workspace/dokstud/alpenglow/data/{stripe_id:06d}/{stripe_id:06d}_{version_id:05d}.tif', [0, 1, 2], list(range(1, 1801))],
                                     kwargs={}
                                 )
                                 ))

    runner = AlpenglowRunner(config)

    for image_id in get_image_order(config):
        log(3, 'apply {}'.format(image_id))
        runner.apply(image_id)


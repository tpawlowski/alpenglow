from alpenglow.benchmark import BenchmarkConfig, get_image_order, is_in_sample, get_image_source, CorrelationState, \
    ShiftState, PositionState, DelayDownloadState, MergeImageState


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
        self.completed_up_to = -1


    def apply(self, image_id):
        stripe, version = image_id

        # don't download samples from stripe N unless all data from stripe N-2 is printed
        if is_in_sample(self.config, image_id[1]):
            self.image_source.get_image_future(stripe, version)
        else:
            if self.delay_download_state.apply_image_id(stripe, version):

if __name__ == '__main__':
    config = BenchmarkConfig()

    runner = AlpenglowRunner(config)

    for image_id in get_image_order(config):
        runner.apply(image_id)


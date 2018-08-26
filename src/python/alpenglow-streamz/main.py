import time
from streamz import Stream

from alpenglow.benchmark import BenchmarkConfig, get_image_order, is_in_sample, get_image_source, CorrelationState, \
    ShiftState, PositionState
from dask.distributed import Client


def get_image(image_id, config=None):
    stripe, version = image_id
    return [stripe, version, get_image_source(config).get_image(stripe, version)]

def correlation(state, image):
    print("correlation {}".format(image[:2]))
    result = state.apply(image[1], image[0], image[2])
    return state, result

def shifts(state, correlations):
    results = []
    for correlation in correlations:
        shift = state.apply(correlation[0], correlation[1], correlation[2])
        if shift is not None:
            results.append(shift)

    print("shifts {}".format(results))
    return state, results

def positions(state, shifts):
    results = []
    for shift_metadata in shifts:
        stripe, shift, shape = shift_metadata
        for position in state.apply(stripe, shift, shape):
            for version in range(state.config.version_count):
                results.append([version] + list(position))

    print("position {}".format(results))
    return state, results


if __name__ == '__main__':
    config = BenchmarkConfig()

    client = Client()

    image_id_bolt = Stream()
    sampling_bolt = image_id_bolt.filter(lambda x: is_in_sample(config, x[1]))
    get_sample_images_bolt = sampling_bolt.scatter()\
        .map(get_image, config=config).buffer(8)\
        .accumulate(correlation, returns_state=True, start=CorrelationState(config)).buffer(8)\
        .accumulate(shifts, returns_state=True, start=ShiftState(config)).buffer(8)\
        .accumulate(positions, returns_state=True, start=PositionState(config)).buffer(8)\
        .gather().flatten().sink(print)

    for image_id in get_image_order(config):
        image_id_bolt.emit(image_id)

    try:
        time.sleep(30)
    finally:
        client.close()

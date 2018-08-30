import time
from streamz import Stream

from alpenglow.benchmark import BenchmarkConfig, get_image_order, is_in_sample, get_image_source, CorrelationState, \
    ShiftState, PositionState, DelayDownloadState, MergeImageState
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

def delay_images(state, data):
    results = []
    if data[0] == 'id':
        stripe, version = data[1]
        if state.apply_image_id(stripe, version):
            results.append([stripe, version])
    else:
        for position in data[1]:
            version = position[0]
            stripe = position[1]
            print("all images accept position {} {}".format(version, stripe))
            if state.apply_metadata(stripe, version):
                results.append([stripe, version])

    return state, results

def output_image(state, data):
    to_emit = []
    if data[0] == 'image':
        (stripe, version, image) = data[1]
        to_emit.extend(state.apply_image(version, stripe, image))
    else:
        for position in data[1]:
            to_emit.extend(state.apply_metadata(position))

    return state, to_emit


def print_x(x):
    print(str(x))
    return x


if __name__ == '__main__':
    config = BenchmarkConfig()

    buffer_size = 16
    client = Client('127.0.0.1:8786')

    image_id_bolt = Stream()
    sampling_bolt = image_id_bolt.filter(lambda x: is_in_sample(config, x[1]))
    sample_images_bolt = sampling_bolt.scatter()\
        .map(get_image, config=config).buffer(buffer_size)

    positions_bolt = sample_images_bolt\
        .accumulate(correlation, returns_state=True, start=CorrelationState(config)).buffer(buffer_size)\
        .accumulate(shifts, returns_state=True, start=ShiftState(config)).buffer(buffer_size)\
        .accumulate(positions, returns_state=True, start=PositionState(config)).buffer(buffer_size)\
        .map(lambda x: ['positions', x]).buffer(buffer_size)

    all_images = image_id_bolt.scatter().map(lambda x: ['id', x]).buffer(buffer_size).union(positions_bolt)\
        .accumulate(delay_images, returns_state=True, start=DelayDownloadState(config)).buffer(buffer_size) \
        .gather().flatten().map(print_x).scatter().buffer(buffer_size).map(get_image, config=config).map(print_x).buffer(buffer_size)\
        .union(sample_images_bolt)

    output_stream = all_images.buffer(buffer_size).map(lambda x: ['image', x]).buffer(buffer_size)\
        .union(positions_bolt).buffer(buffer_size)\
        .accumulate(output_image, returns_state=True, start=MergeImageState(config)).buffer(buffer_size)\
        .gather().flatten().map(lambda x: [x[0], x[2], x[2] + x[1].shape[0]]).sink(print)

    for image_id in get_image_order(config):
        image_id_bolt.emit(image_id)

    try:
        time.sleep(30)
    finally:
        client.close()

import time
from streamz import Stream

from alpenglow.benchmark import BenchmarkConfig, get_image_order, is_in_sample, get_image_source, CorrelationState, \
    ShiftState, PositionState, DelayDownloadState, MergeImageState
from dask.distributed import Client


def get_images(image_ids, config=None):
    if len(image_ids) == 0:
        return []
    source = get_image_source(config)
    return [[stripe, version, source.get_image(stripe, version)] for stripe, version in image_ids]


def sample(image_id, config=None):
    _, version = image_id
    if is_in_sample(config, version):
        return [image_id]
    return []

def correlation(state, images):
    results = []
    for stripe, version, image in images:
        print("apply image ({}, {}) to correlation".format(stripe, version))
        results.extend(state.apply(version, stripe, image))
    return state, results

def shifts(state, correlations):
    results = []
    for stripe, correlation, shape in correlations:
        shift = state.apply(stripe, correlation, shape)
        if shift is not None:
            results.append(shift)

    print("shifts {}".format(results))
    return state, results

def positions(state, shifts):
    results = []
    for stripe, shift, shape in shifts:
        for position in state.apply(stripe, shift, shape):
            results.extend([[version] + list(position) for version in range(state.config.version_count)])

    print("position {}".format(results))
    return state, results

def delay_images(state, data):
    results = []
    if data[0] == 'id':
        for stripe, version in data[1]:
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
        for stripe, version, image in data[1]:
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

    buffer_size = 32
    client = Client('127.0.0.1:8786')

    image_id_bolt = Stream()
    scattered_ids = image_id_bolt.scatter()
    sample_images_bolt = scattered_ids\
        .map(sample, config=config).buffer(buffer_size)

    positions_bolt = sample_images_bolt\
        .accumulate(correlation, returns_state=True, start=CorrelationState(config)).buffer(buffer_size) \
        .accumulate(shifts, returns_state=True, start=ShiftState(config)).buffer(buffer_size) \
        .accumulate(positions, returns_state=True, start=PositionState(config)).buffer(buffer_size)\
        .map(lambda x: ['positions', x]).buffer(buffer_size)

    all_images = scattered_ids.map(lambda x: ['id', [x]]).buffer(buffer_size)\
        .union(positions_bolt).buffer(buffer_size)\
        .accumulate(delay_images, returns_state=True, start=DelayDownloadState(config)).buffer(buffer_size) \
        .map(get_images, config=config).buffer(buffer_size)\
        .union(sample_images_bolt).buffer(buffer_size)

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

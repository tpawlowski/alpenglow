from streamz import Stream
from dask.distributed import Client


def sample(image_id):
    _, version = image_id
    if ((version + 1) * (3 - 1) // 7) > (version * (3 - 1) // 7):
        return [image_id]
    return []

client = Client('127.0.0.1:8786')
image_ids = Stream()
part_1 = image_ids.scatter().map(sample).buffer(10).gather().sink(print)
for stripe in range(3):
    for version in range(7):
        image_ids.emit((stripe, version))


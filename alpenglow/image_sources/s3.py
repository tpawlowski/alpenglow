from concurrent.futures import Future
import sys
is_py2 = sys.version[0] == '2'
if is_py2:
    from Queue import Queue, Empty
else:
    from queue import Queue, Empty

from threading import Thread, Lock

import boto3
from io import BytesIO

from alpenglow.image_sources.image_source import ImageSource
import skimage.external.tifffile as tiff


class S3ImageSourceThread(Thread):
    def __init__(self, thread_id, credentials, task_queue, threads, lock, array_mapping):
        Thread.__init__(self)
        self.daemon = True
        self.thread_id = thread_id
        self.threads = threads
        self.task_queue = task_queue
        self.lock = lock
        self._bucket = credentials['bucket']
        self.connection = None
        self._credentials = credentials
        self.array_mapping = array_mapping


    def run(self):
        try:
            while True:
                path, future, stripe_id, stripe_count = self.task_queue.get_nowait()
                image_data = BytesIO(self.get_connection().get_object(Bucket=self._bucket, Key=path)["Body"].read())
                future.set_result(ImageSource.loop_image(self.array_mapping(tiff.TiffFile(image_data).asarray()), stripe_id, stripe_count))
        except Empty:
            self.lock.acquire()
            del self.threads[self.thread_id]
            self.lock.release()

    def get_connection(self):
        if self.connection is None:
            self.connection = boto3.client('s3', endpoint_url=self._credentials['endpoint'],
                                           aws_access_key_id=self._credentials['key'],
                                           aws_secret_access_key=self._credentials['secret'])
        return self.connection


class S3ImageSource(ImageSource):
    """
    Implementation of image source fetching images from s3 storage.
    """
    def __init__(self, path_format, stripe_ids, version_ids, key, secret, bucket, endpoint, channel_count=1, mapping=None, max_workers=8, array_mapping=None):
        self.path_format = path_format
        self.stripe_ids = stripe_ids
        self.version_ids = version_ids
        self._channel_count = channel_count
        self._max_workers = max_workers
        self.mapping = mapping
        self._array_mapping = array_mapping
        if array_mapping is None:
            self._array_mapping = lambda a: a.swapaxes(0, 1)

        self._bucket = bucket

        self._thread_data = {
            'bucket': bucket,
            'endpoint': endpoint,
            'key': key,
            'secret': secret
        }
        self._task_queue = Queue()
        self._lock = Lock()
        self._threads = {}
        self._thread_id = 1

    def get_image(self, stripe_id, version_id):
        return self.get_image_future(stripe_id, version_id).result()

    def get_image_future(self, stripe_id, version_id):
        stripe_image_id = stripe_id % len(self.stripe_ids)
        if (stripe_id // len(self.stripe_ids)) % 2 == 1:
            stripe_image_id = len(self.stripe_ids) - 1 - stripe_image_id

        external_stripe_id = self.stripe_ids[stripe_image_id]
        external_version_id = self.version_ids[version_id]

        if self.mapping is not None:
            external_stripe_id, external_version_id = self.mapping(external_stripe_id, external_version_id)

        path = self.path_format.format(stripe_id=external_stripe_id, version_id=external_version_id).lstrip('/')

        future = Future()

        task = (path, future, stripe_id, len(self.stripe_ids))
        self._task_queue.put(task)
        self._lock.acquire()
        if len(self._threads) < self._max_workers:
            thread_id = self._thread_id
            self._thread_id += 1
            thread = S3ImageSourceThread(thread_id, self._thread_data, self._task_queue, self._threads, self._lock, self._array_mapping)
            self._threads[thread_id] = thread
            thread.start()
        self._lock.release()

        return future

    def stripe_count(self):
        return len(self.stripe_ids)

    def version_count(self):
        return len(self.version_ids)

    def channel_count(self):
        return self._channel_count

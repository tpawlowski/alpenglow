from concurrent.futures import Future
from threading import Thread, Lock
from alpenglow.image_sources.image_source import ImageSource


class ImageSourceThread(Thread):
    def __init__(self, image_source, task_queue, lock, sources):
        Thread.__init__(self)
        self.daemon = True
        self.task_queue = task_queue
        self.lock = lock
        self.image_source = image_source
        self.sources = sources

    def run(self):
        while True:
            self.lock.acquire()
            if len(self.task_queue) == 0:
                break
            future, stripe_id, version_id = self.task_queue.pop(0)
            self.lock.release()
            future.set_result(self.image_source.get_image(stripe_id, version_id))
        self.sources.append(self.image_source)
        self.lock.release()


class ThreadedImageSource(ImageSource):
    def __init__(self, sources):
        self.sources = sources
        self.sample_source = sources[0]
        self._task_queue = []
        self._lock = Lock()
        self._threads = {}

    def get_image_future(self, stripe_id, version_id):
        future = Future()
        task = (future, stripe_id, version_id)
        self._lock.acquire()
        self._task_queue.append(task)
        if len(self.sources) > 0:
            image_source = self.sources.pop()
            thread = ImageSourceThread(image_source, self._task_queue, self._lock, self.sources)
            thread.start()
        self._lock.release()
        return future

    def get_image(self, stripe_id, version_id):
        return self.get_image_future(stripe_id, version_id).result()

    def stripe_count(self):
        return self.sample_source.stripe_count()

    def version_count(self):
        return self.sample_source.version_count()

    def channel_count(self):
        return self.sample_source.channel_count()


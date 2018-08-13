import logging
import sys
import time

import winton_kafka_streams.kafka_config as kafka_config
import winton_kafka_streams.kafka_streams as kafka_streams
from winton_kafka_streams.processor import TopologyBuilder, BaseProcessor

log = logging.getLogger(__name__)


class PipeProcessor(BaseProcessor):
    def initialise(self, _name, _context):
        super().initialise(_name, _context)

    def process(self, key, value):
        self.context.forward(key, value)

    def punctuate(self, timestamp):
        pass

def run(config_file):
    kafka_config.read_local_config(config_file)

    with TopologyBuilder() as topology_builder:
        topology_builder. \
            source('input-value', ['logs-input']). \
            sink('output-value', 'logs-debug', 'input-value')

    wks = kafka_streams.KafkaStreams(topology_builder, kafka_config)
    wks.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        wks.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Debug runner for Python Kafka Streams")
    parser.add_argument('--config-file', '-c',
                        help="Local configuration - will override internal defaults",
                        default='config.properties')
    parser.add_argument('--verbose', '-v',
                        help="Increase versbosity (repeat to increase level)",
                        action='count', default=0)
    args = parser.parse_args()

    levels = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}
    level = levels.get(args.verbose, logging.DEBUG)
    logging.basicConfig(stream=sys.stdout, level=level)
    run(args.config_file)

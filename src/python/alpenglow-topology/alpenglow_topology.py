# Import Grouping and TopologyBuilder from heronpy

# Import the defined Bolts and Spouts
from heronpy.api.stream import Grouping
from heronpy.api.topology import TopologyBuilder

from image_ready_spout import ImageReadySpout
from sampling_bolt import SamplingBolt
from get_demo_image_bolt import GetDemoImageBolt
from correlations_bolt import CorrelationsBolt
from shifts_bolt import ShiftsBolt
from absolute_positions_bolt import AbsolutePositionsBolt
from output_image_bolt import OutputImageBolt
from delay_image_download_bolt import DelayImageDownloadBolt
from windowing_bolt import WindowingBolt
from segmentation_bolt import SegmentationBolt

if __name__ == '__main__':
    builder = TopologyBuilder("Alpenglow_Topology")

    config = {
        "benchmark_config": dict(verbosity=1,
                                 replication_factor=3,
                                 sample_size=8,
                                 window_length=256,
                                 window_step=128,
                                 image_source="filesystem",
                                 image_source_config=dict(
                                     args=['/Users/tpawlowski/workspace/dokstud/alpenglow/data/{stripe_id:06d}/{stripe_id:06d}_{version_id:05d}.tif', [0, 1, 2], list(range(1, 1801, 60))],
                                     kwargs={}
                                 )
                                 )
    }

    # Emits information that images are ready for download
    image_id_bolt = builder.add_spout("image_ready_spout", ImageReadySpout, par=1, config=config)

    # Sample input stream keeping only given number of ids from each stripe
    sampling_bolt = builder.add_bolt("sampling_bolt",
                                     SamplingBolt,
                                     par=1,
                                     inputs={image_id_bolt: Grouping.fields('version')},
                                     config=config)

    # Downloads images for sampled ids
    get_sample_images_bolt = builder.add_bolt("get_sample_images_bolt",
                                              GetDemoImageBolt,
                                              par=8,
                                              inputs={sampling_bolt: Grouping.fields('stripe', 'version')},
                                              config=config)

    correlations_bolt = builder.add_bolt("correlations_bolt",
                                         CorrelationsBolt,
                                         par=8,
                                         inputs={get_sample_images_bolt: Grouping.fields('version')},
                                         config=config)

    shifts_bolt = builder.add_bolt("shifts_bolt",
                                   ShiftsBolt,
                                   par=4,
                                   inputs={correlations_bolt: Grouping.fields('stripe')},
                                   config=config)

    absolute_positions_bolt = builder.add_bolt("absolute_positions_bolt", AbsolutePositionsBolt, par=1,
                                               inputs={shifts_bolt: Grouping.fields('stripe')},
                                               config=config)

    delay_image_download_bolt = builder.add_bolt("delay_download_bolt", DelayImageDownloadBolt, par=1,
                                                 inputs={absolute_positions_bolt: Grouping.fields('stripe', 'version'),
                                                         image_id_bolt: Grouping.fields('stripe', 'version')},
                                                 config=config)

    get_rest_images_bolt = builder.add_bolt("get_images_bolt", GetDemoImageBolt, par=8,
                                       inputs={delay_image_download_bolt: Grouping.fields('stripe', 'version')},
                                       config=config)

    output_images_bolt = builder.add_bolt("output_images_bolt", OutputImageBolt, par=4,
                                          inputs={get_rest_images_bolt: Grouping.fields('version'),
                                                  get_sample_images_bolt: Grouping.fields('version'),
                                                  absolute_positions_bolt: Grouping.fields('version')},
                                          config=config)

    windowing_bolt = builder.add_bolt("windowing_bolt", WindowingBolt, par=1,
                                      config=config,
                                      inputs={output_images_bolt: Grouping.ALL})

    segmentation_bolt = builder.add_bolt("segmentation_bolt", SegmentationBolt, par=3, config=config,
                                         inputs={windowing_bolt: Grouping.SHUFFLE})

    # Finalize the topology graph
    builder.build_and_submit()

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
from save_image_to_file_bolt import SaveImageToFileBolt
from delay_image_download_bolt import DelayImageDownloadBolt

if __name__ == '__main__':
    builder = TopologyBuilder("Alpenglow_Topology")

    config = {
        "benchmark_config": dict(verbosity=1, version_count=5, stripe_count=18)
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

    output_to_tmp_dir = builder.add_bolt("output_to_tmp_dir", SaveImageToFileBolt, par=2,
                                         inputs={output_images_bolt: Grouping.fields('version')})

    # Finalize the topology graph
    builder.build_and_submit()

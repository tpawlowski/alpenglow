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

if __name__ == '__main__':
    # Define the topology name
    builder = TopologyBuilder("Alpenglow_Topology")

    VERSION_COUNT = 5
    STRIPE_COUNT = 7
    N = 3
    MARGIN = 10

    # Define the topology dag

    # Start with the demo image_id spout
    config = {
        'version_count': VERSION_COUNT,
        'stripe_count': STRIPE_COUNT
    }
    image_id_bolt = builder.add_spout("image_ready_spout", ImageReadySpout, par=1, config=config)

    # Sample input stream keeping only given number of ids from each stripe
    sampling_config = {
        'sample_size': N,
        'version_count': VERSION_COUNT
    }
    sampling_inputs = {
        image_id_bolt: Grouping.fields('version')
    }
    sampling_bolt = builder.add_bolt("sampling_bolt", SamplingBolt, par=1,
                                     inputs=sampling_inputs, config=sampling_config)

    # download images for sampled ids
    get_sample_images_bolt_config = {
        "image_source_config": {
            "stripe_count": STRIPE_COUNT,
            "version_count": VERSION_COUNT,
            "channel_count": 1,
            "vertical_shifts": (19, 38, 0),
            "overlap": 0.4,
        }
    }
    get_sample_images_bolt = builder.add_bolt("get_sample_images_bolt", GetDemoImageBolt, par=2,
                                              inputs={sampling_bolt: Grouping.fields('version')},
                                              config=get_sample_images_bolt_config)

    correlations_bolt = builder.add_bolt("correlations_bolt", CorrelationsBolt, par=2,
                                         inputs={get_sample_images_bolt: Grouping.fields('version')})

    shifts_bolt = builder.add_bolt("shifts_bolt", ShiftsBolt, par=1,
                                   inputs={correlations_bolt: Grouping.fields('stripe')},
                                   config={"sample_size": N})

    absolute_positions_bolt = builder.add_bolt("absolute_positions_bolt", AbsolutePositionsBolt, par=1,
                                               inputs={shifts_bolt: Grouping.fields('stripe')},
                                               config={"margin": MARGIN, "version_count": VERSION_COUNT})

    get_images_bolt = builder.add_bolt("get_images_bolt", GetDemoImageBolt, par=4,
                                       inputs={image_id_bolt: Grouping.fields('version')},
                                       config=get_sample_images_bolt_config)

    output_images_bolt = builder.add_bolt("output_images_bolt", OutputImageBolt, par=2,
                                          inputs={get_images_bolt: Grouping.fields('version'),
                                                  absolute_positions_bolt: Grouping.fields('version')})

    output_to_tmp_dir = builder.add_bolt("output_to_tmp_dir", SaveImageToFileBolt, par=1,
                                         inputs={output_images_bolt: Grouping.fields('version')})

    # Finalize the topology graph
    builder.build_and_submit()

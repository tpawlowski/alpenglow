benchmark_config = dict(
    verbosity=1,
    sample_size=3,
    replication_factor=20,
    window_length=256,
    window_step=128,
    image_source="demo"
)

# dict(verbosity=1,
#      replication_factor=7,
#      sample_size=25,
#      window_length=256,
#      window_step=128,
#      image_source="filesystem",
#      image_source_config=dict(
#          args=[
#              '/Users/tpawlowski/workspace/dokstud/alpenglow/data/{stripe_id:06d}/{stripe_id:06d}_{version_id:05d}.tif',
#              [0, 1, 2], list(range(1, 1801, 60))],
#          kwargs={}
#      )
# )
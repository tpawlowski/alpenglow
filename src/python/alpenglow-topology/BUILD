python_library(
    name = "spouts-bolts-py",
    sources=globs('*.py', exclude=[['alpenglow_topology.py']]),
    dependencies = [
        '3rdparty/python:alpenglow'
    ]
)

python_binary(
    name = "alpenglow-topology",
    source='alpenglow_topology.py',
    dependencies = [
        ':spouts-bolts-py',
        '3rdparty/python:heronpy',
        '3rdparty/python:six',
        '3rdparty/python:protobuf',
        '3rdparty/python:numpy',
        '3rdparty/python:scikit-image',
        '3rdparty/python:boto3',
        '3rdparty/python:matplotlib',
        '3rdparty/python:scipy',
        '3rdparty/python:alpenglow'
    ],
)

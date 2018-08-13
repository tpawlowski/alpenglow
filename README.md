# alpenglow
LSMstitch software for stitching a 3D volume from individual tiff frames captured by our custom-built light-sheet microscope.

# Installation

## Python version

This code was tested on python 2.7.15. Some of used libraries raise warnings when trying to use python 3. 

## Virtualenv

This step is not required, but running this program in python virtual environment separates it from other programs run on the same machine. To install virtualenv follow the [documentation](https://virtualenv.pypa.io/en/stable/installation/).

```
virtualenv -p python venv
source venv/bin/activate
```

## Alpenglow library
```
python setup.py install
```

## Notebooks dependencies

```
pip install jupyter

pip install ipykernel
python -m ipykernel install --user --name=venv
```

Before running notebooks change the jupyters kernel to venv. In top menu select "Kernel -> Change kernel -> venv".

# Heron pipeline

## Installation

### Heron

open https://github.com/apache/incubator-heron/releases and download proper heron install script.
```
wget https://github.com/apache/incubator-heron/releases/download/0.17.8/heron-install-0.17.8-darwin.sh
chmod +x heron-*.sh
```

Install in `~/.heron/` with command: 
```
./heron-install-0.17.8-darwin.sh --user
```

Afterwards make sure that `~/bin` is in the path. If you don't want to add just prefix each heron execution with `~/bin/`.



### Pants

Pants script is already included in the repo

### Python

```
virtualenv -p python venv_heron
source venv_heron/bin/activate
pip install -r requirements_heron.txt
python setup.py install
```

## Building

Heron cluster requires bundling a topology with all its dependencies before submitting. Following command will do that.
```
./pants binary src/python/alpenglow-topology
```

## Submitting
following command pushes the .pex topology to heron cluster:
```
heron submit local --deploy-deactivated dist/alpenglow-topology.pex - Alpenglow_Topology
```

## Starting

Note: you need to wait couple of seconds before the topology becomes ready to activate.
```
heron activate local Alpenglow_Topology
```

## Monitoring

You can monitor the execution of the topology either with `heron-tracker`, `heron-ui` and visiting `http://localhost:8889` or by reading logs from: `~/.herondata/topologies/local/tpawlowski/Alpenglow_Topology/log-files`.

## Stoping
```
heron deactivate local Alpenglow_Topology
```

## Cleaning (removing topology from cluster)

```
heron kill local Alpenglow_Topology
```

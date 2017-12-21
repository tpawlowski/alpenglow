# alpenglow
LSMstitch software for stitching a 3D volume from individual tiff frames captured by our custom-built light-sheet microscope.

# Installation

## Virtualenv

This step is not required, but running this program in python virtual environment separates it from other programs run on the same machine. To install virtualenv follow the [documentation](https://virtualenv.pypa.io/en/stable/installation/).

```
virtualenv -p python3 venv
source venv/bin/activate
```

## Alpenglow library
```
python setup.py install
```

## Notebooks dependencies

```
git clone https://github.com/gallantlab/cottoncandy.git
cd cottoncandy
python setup.py install
cd -

pip install jupyter

pip install ipykernel
python -m ipykernel install --user --name=venv
```

Before running notebooks change the jupyters kernel to venv. In top menu select "Kernel -> Change kernel -> venv".

[![PyPI](https://img.shields.io/pypi/v/appbundler.svg?style=flat-square)](https://pypi.org/pypi/appbundler)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/appbundler.svg?style=flat-square)
[![Build Status](https://travis-ci.com/mab4058/appbundler.svg?branch=master)](https://travis-ci.com/mab4058/appbundler)
![GitHub](https://img.shields.io/github/license/mab4058/appbundler.svg?style=flat-square)

# appbundler

Zip and app, all it's dependencies, and any other data.

## Installation

`pip install appbundler`

## Usage

After installation you will be able to run:

`appbundler /path/to/appbundler.toml`

The `appbundler.toml` config file must exist in the app's root directory.

Alternatively,

`python -m appbundler -h`

## appbundler.toml

The `appbundler.toml` contains app information such as the package/library 
being installed, any additional 'supplemental' data to be brought into the 
build.

Data examples:
* [data.example1]
    * The whole `root` directory will be copied to the build directory and the directory structure will be preserved.
* [data.example2]
    * Any csv file in the `sub_directory` of `root` will be copied to the build directory and the directory structure will be preserved.
* [data.example3]
    * All json files in entirety of the `root` directory will be recursively copied to the build directory.  Also, due to `flatten` all file will be copied to the root of the build directory.

```toml
# Example appbundler configuration file.

package="myapp"

[data]

  [data.example1]
  root="/user/example1"

  [data.example2]
  root="/user/example2"
  sub_directory="/sub"
  pattern="*.csv"
  
  [data.example3]
  root="./example3"
  pattern="*.json"
  recursive=true
  flatten=true
```

### Basic flow

1. App requirements will be installed via `requirements.txt`, `setup.py`, or `pyproject.toml` files.
2. Clean up the directories by removing `__pycache__` and `.pyc` files.  Reduce the zip file size as much as possible.
3. Handle all supplemental data.
4. Zip the build directory.

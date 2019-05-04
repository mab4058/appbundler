[![PyPI](https://img.shields.io/pypi/v/appbundler.svg?style=flat-square)](https://pypi.org/pypi/appbundler)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/appbundler.svg?style=flat-square)
![GitHub](https://img.shields.io/github/license/mab4058/appbundler.svg?style=flat-square)

# appbundler

Zip and app, all it's dependencies, and any other data.

# Installation

`pip install appbundler`

# Usage

After installation you will be able to run:

`appbundler -h`

Alternatively,

`python -m appbundler -h`

# appbundler.toml

The `appbundler.toml` contains app information such as the package/library 
being installed, any additional 'supplemental' data to be brought into the 
build.

In this example the whole directory `"/user/value_data"` will be copied to
the build and any `.csv` file in `"/user/account_data/public"` will also
be copied.  All paths are preserved from the `root` dir.

```toml
# Example appbundler configuration file.

title = "Appbundler configuration example."

[package]
name="myPackage"
path="./myPackage"

[data]

[data.values]
root="/user/value_data"

[data.accounts]
root="/user/account_data"
sub_directory="/public"
pattern="*.csv"
```
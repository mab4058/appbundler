import ast
import re
from pathlib import Path

from setuptools import find_packages
from setuptools import setup

CURRENT_DIR = Path(__file__).parent


def get_version():
    """
    Gets the version from __init__.

    Credit:
        This function was adapted from python/black on Github.

    Returns:
        str: Version string.

    """
    init_file = CURRENT_DIR.joinpath('appbundler/__init__.py')
    _version_re = re.compile(r"__version__\s+=\s+(?P<version>.*)")
    with open(init_file, "r", encoding="utf8") as f:
        match = _version_re.search(f.read())
        version = match.group("version") if match is not None else '"unknown"'
    return str(ast.literal_eval(version))


setup(name='appbundler',
      version=get_version(),
      description='Bundle an app, dependencies, and any other files into a neat zip file.',
      author='Michael Bayer',
      author_email='mab4058@gmail.com',
      url='https://github.com/mab4058/appbundler',
      license='MIT',
      install_requires=['toml>=0.10.0,<1.0.0'],
      extras_require={
          'tests': ['pytest>=3.5.0,<4.0.0'],
      },
      entry_points={
          'console_scripts': ['appbundler = appbundler.__main__:main']
      },
      python_requires='>=3.6',
      classifiers=[
          'Development Status :: 1 - Planning',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3 :: Only',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Topic :: Software Development :: Libraries',
          'Topic :: Software Development :: Libraries :: Python Modules'
      ],
      packages=find_packages())

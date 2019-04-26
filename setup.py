from setuptools import find_packages
from setuptools import setup

version = '0.0.0'

setup(name='appbundler',
      version=version,
      description='Bundle an app, dependencies, and any other files into a neat zip file.',
      author='Michael Bayer',
      author_email='mab4058@gmail.com',
      url='https://github.com/mab4058/appbundler',
      download_url='https://github.com/mab4058/appbundler/archive/{}.tar.gz'.format(version),
      license='MIT',
      install_requires=['toml>=0.10.0,<1.0.0'],
      extras_require={
          'tests': ['pytest>=3.5.0,<4.0.0'],
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

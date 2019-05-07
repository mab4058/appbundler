from pathlib import Path

from setuptools import setup

CURRENT_DIR = Path(__file__).parent


def get_version():
    with open('appbundler/__version__.py') as fp:
        tmp = {}
        exec(fp.read(), tmp)
        return tmp['__version__']


setup(name='appbundler',
      version=get_version(),
      description='Bundle an app, dependencies, and any other files into a zip file.',
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
      packages=['appbundler'])

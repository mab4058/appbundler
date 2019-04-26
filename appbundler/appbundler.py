import functools
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

import toml

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
logger.setLevel(logging.DEBUG)


def log_entrance_exit(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info('Entering %s.', func.__name__)
        results = func(*args, **kwargs)
        logger.info('Exiting %s.', func.__name__)
        return results

    return wrapper


class cd:
    """Context manager for temporary cd."""

    def __init__(self, destiation):
        self.original_dir = os.getcwd()
        self.new_dir = destiation

    def __enter__(self):
        os.chdir(self.new_dir)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.original_dir)


class Config:
    def __init__(self, config_file):
        self.config = toml.load(config_file)

    @property
    def package(self):
        return self.config['package']

    @property
    def data(self):
        return self._parse_and_verify(self.config['data'])

    @staticmethod
    def _parse_and_verify(data):
        """
        Parses the paths and verifies their existence.

        Args:
            data (dict): Dictionary containing paths as values.

        Returns:
            dict: Dictionary with the same keys, but Path instances as values.

        Raises:
            ValueError: If path does not exist.

        """

        new = {}
        for k, v in data.items():
            path = Path(v)
            if not path.exists():
                raise ValueError('Path does not exist: %s', v)
            else:
                new[k] = path.resolve()
        return new


class AppBundler:
    """
    Handles bundling all dependencies and supplemental data into a nice zip file.

    All path must be absolute or relative to app_directory.
    """

    def __init__(self, app_directory, package_name=None, supplemental_data=None, build_directory=None):
        self.app_directory = Path(app_directory).resolve()
        self.package_name = package_name
        self.supplemental_data = supplemental_data
        self.build_directory = build_directory

        # Compute paths.
        if package_name is None:
            self.package = None
        else:
            self.package = self.app_directory.joinpath(package_name).resolve()

        if build_directory is None:
            self.build_directory = self.app_directory.joinpath('build')
        else:
            self.build_directory = Path(build_directory).joinpath('build').resolve()

    @log_entrance_exit
    def run(self):
        """Runs all steps of the bundling process."""

        try:
            self.build_directory.mkdir(parents=True)
        except FileExistsError:
            logger.warning('Directory already exists: %s', self.build_directory)
            decision = input(f'{self.build_directory} already exists. Overwrite? Y/[N]: ')
            if decision.strip().upper() == 'Y':
                logger.info('Deleting old build directory: %s', self.build_directory)
                shutil.rmtree(self.build_directory)
                self.build_directory.mkdir(parents=True)
            else:
                return

        self._install_dependencies()
        self._cleanup_files()

    @log_entrance_exit
    def _install_dependencies(self):
        """Installs dependencies contained in requirements.txt or setup.py."""

        requirements_file = self.app_directory.joinpath('requirements.txt')
        setup_file = self.app_directory.joinpath('setup.py')

        package_copy_required = False
        if requirements_file.exists():
            cmd = [sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file), '-t',
                   str(self.build_directory)]
            package_copy_required = True
        elif setup_file.exists():
            cmd = [sys.executable, '-m', 'pip', 'install', str(setup_file.parent), '-t', str(self.build_directory)]
        else:
            raise ValueError('Could not locate requirements.txt or setup.py.')

        logger.debug('Running subprocess cmds: %s', cmd)
        _ = subprocess.run(cmd, check=True)

        if package_copy_required:
            shutil.copytree(self.package_name, self.build_directory)

    @log_entrance_exit
    def _cleanup_files(self):
        """Removes __pycache__ and .pyc files resulting from installation."""

        for root, dirs, files in os.walk(self.build_directory):
            dirs_to_delete = [Path(root).joinpath(x) for x in dirs if x == '__pycache__']
            files_to_delete = [Path(root).joinpath(x) for x in files if Path(x).suffix == '.pyc']
            for d in dirs_to_delete:
                logger.info('Deleting: %s', d)
                shutil.rmtree(d)
            for f in files_to_delete:
                logger.info('Deleting: %s', f)
                f.unlink()

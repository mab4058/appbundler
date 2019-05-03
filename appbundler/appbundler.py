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


class SupplementalData:
    """
    Handles finding files based on a glob pattern.

    Directory structure will be preserved unless an override is provided.
    In the case of an override all files will be moved to the specified
    override directory.

    Args:
        directory (str, pathlib.Path): Base data directory to be included in
            build.
        sub_directories (list of str): Optional sub-directory path(s) in
            'directory'. This can be used to limit what is copied.
        pattern (str): Optional glob filtering.

    Attributes:
        directory (pathlib.Path): Base data directory to be included in build.
        sub_directories (list of str): sub-directory path(s) in 'directory' if
            any were specified.
        locations_to_copy (list of pathlib.Path): List of all directories/files
            to be copied.

    """

    def __init__(self, directory, sub_directories=None, pattern=None):
        self.directory = Path(directory)
        self.sub_directories = sub_directories
        self.pattern = pattern
        self.locations_to_copy = []

        locations = []
        if self.sub_directories is None:
            locations.append(self.directory)
        else:
            for sub in self.sub_directories:
                sub = sub.lstrip('/\\')
                current = self.directory.joinpath(sub)
                if not current.exists():
                    logger.error('Directory does not exist: %s', current)
                    raise ValueError(f'Directory does not exist: {current}')
                self.locations_to_copy.append(current)

        if self.pattern is None:
            [logger.info('Will copy: %s', x) for x in locations]
            self.locations_to_copy = locations
        else:
            for location in locations:
                files = list(location.glob(self.pattern))
                [logger.info('Will copy: %s', x) for x in files]
                self.locations_to_copy.extend(files)


class AppBundler:
    """
    Handles bundling all dependencies and supplemental data into a nice zip file.

    All path must be absolute or relative to app_directory.

    Args:
        app_directory (str, pathlib.Path): Root app directory. This is
            typically the directory containing the appbundler.toml file.
        package_name (str): Python package name. Must exist in the
            app_directory.
        supplemental_data (list of SupplementalData): Optional list of
            SupplementalData instances. The files or directories defined in
                these instances will be included in the zip file.
        build_directory (str, pathlib.Path): Optional build directory override.
            Default is in the app_directory.
        make_zip (bool): Create a zip file of the build contents. Optional and
            defaults to True.

    """

    def __init__(
            self, app_directory, package_name, supplemental_data=None,
            build_directory=None, make_zip=True
    ):
        self.app_directory = Path(app_directory).resolve()
        self.package_name = package_name
        self.supplemental_data = supplemental_data
        self.build_directory = build_directory
        self.make_zip = make_zip

        # Compute paths.
        self.package_dir = self.app_directory.joinpath(package_name).resolve()

        if build_directory is None:
            self.build_directory = self.app_directory.joinpath('build')
        else:
            self.build_directory = Path(build_directory).joinpath('build').resolve()

    @log_entrance_exit
    def bundle(self):
        """Runs all steps of the bundling process."""

        try:
            self.build_directory.mkdir(parents=True)
        except FileExistsError:
            logger.warning('Directory already exists: %s', self.build_directory)
            decision = input(
                f'{self.build_directory} already exists. Overwrite? Y/[N]: '
            )
            if decision.strip().upper() == 'Y':
                logger.info('Deleting old build directory: %s', self.build_directory)
                shutil.rmtree(self.build_directory)
                self.build_directory.mkdir(parents=True)
            else:
                return

        self._install_dependencies()
        self._handle_supplemental_data()
        self._cleanup_files()
        if self.make_zip:
            self._zip_files()

    @log_entrance_exit
    def _install_dependencies(self):
        """Installs dependencies contained in requirements.txt or setup.py."""

        requirements_file = self.app_directory.joinpath('requirements.txt')
        setup_file = self.app_directory.joinpath('setup.py')

        package_copy_required = False
        if requirements_file.exists():
            cmd = [
                sys.executable,
                '-m',
                'pip',
                'install',
                '-r',
                str(requirements_file),
                '-t',
                str(self.build_directory),
            ]
            package_copy_required = True
        elif setup_file.exists():
            cmd = [
                sys.executable,
                '-m',
                'pip',
                'install',
                str(setup_file.parent),
                '-t',
                str(self.build_directory),
            ]
        else:
            raise ValueError('Could not locate requirements.txt or setup.py.')

        logger.debug('Running subprocess cmds: %s', cmd)
        _ = subprocess.run(cmd, check=True)

        if package_copy_required:
            shutil.copytree(self.package_dir, self.build_directory)

    @log_entrance_exit
    def _cleanup_files(self):
        """Removes __pycache__ and .pyc files resulting from installation."""

        for root, dirs, files in os.walk(self.build_directory):
            dirs_to_delete = [
                Path(root).joinpath(x) for x in dirs if x == '__pycache__'
            ]
            files_to_delete = [
                Path(root).joinpath(x) for x in files if Path(x).suffix == '.pyc'
            ]
            for d in dirs_to_delete:
                logger.info('Deleting: %s', d)
                shutil.rmtree(d)
            for f in files_to_delete:
                logger.info('Deleting: %s', f)
                f.unlink()

    @log_entrance_exit
    def _handle_supplemental_data(self):
        """Moves any supplemental data into build directory before zip."""

        for data in self.supplemental_data:
            src_base = str(data.directory)
            dst_base = str(self.build_directory.joinpath(data.directory.stem))
            for src in data.locations_to_copy:
                if src.is_dir():
                    for dir_path, dir_names, file_names in os.walk(str(src)):
                        dst_dir = Path(dir_path.replace(src_base, dst_base))
                        if not dst_dir.exists():
                            dst_dir.mkdir(parents=True)
                        for file in file_names:
                            shutil.copy2(os.path.join(dir_path, file), str(dst_dir))
                else:
                    dst_dir = Path(str(src.parent).replace(src_base, dst_base))
                    if not dst_dir.exists():
                        dst_dir.mkdir(parents=True)
                    shutil.copy2(str(src), str(dst_dir))

    @log_entrance_exit
    def _zip_files(self):
        """Zips files in root build_directory."""

        zip_file = Path(self.build_directory.parent).joinpath(
            self.package_name + '.zip'
        )
        logger.info('Creating zip file: %s', zip_file)

        shutil.make_archive(zip_file.with_suffix(''), 'zip', self.build_directory)
        shutil.move(str(zip_file), self.build_directory)

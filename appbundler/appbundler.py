import itertools
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

import toml

from appbundler.utils import cd, log_entrance_exit

logger = logging.getLogger(__name__)


class Config:
    """
    Loads the appbundler.toml file and handles some initial setup.

    All relative paths are relative to the appbundler.toml file.

    Args:
        config_file (str, pathlib.Path): Path to the appbuilder.toml config file.
    """

    def __init__(self, config_file):
        self._file = Path(config_file)
        self._config = toml.load(config_file)

        # Parse all supplemental data locations.
        self._data = []
        with cd(self._file.parent):
            for k, v in self._config.get('data', {}).items():
                root = Path(v['root']).resolve()
                sub_dir = v.get('sub_directories')
                pattern = v.get('pattern')
                recursive = v.get('recursive')
                flatten = v.get('flatten')
                self._data.append(
                    SupplementalData(
                        root,
                        sub_directories=sub_dir,
                        pattern=pattern,
                        recursive=recursive,
                        flatten=flatten,
                    )
                )

    @property
    def package(self):
        return self._config['package']

    @property
    def data(self):
        return self._data


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
        recursive (bool): Optionally use recursive search for pattern.
            Defaults to False.
        flatten (bool): Optionally ignore file structure and copy files
            to the root data directory. Defaults to False.

    Attributes:
        directory (pathlib.Path): Base data directory to be included in build.
        sub_directories (list of str): sub-directory path(s) in 'directory' if
            any were specified.
        locations_to_copy (list of pathlib.Path): List of all directories/files
            to be copied.

    """

    def __init__(
        self,
        directory,
        sub_directories=None,
        pattern=None,
        recursive=False,
        flatten=False,
    ):
        self.directory = Path(directory)
        self.sub_directories = sub_directories
        self.pattern = pattern
        self.recursive = recursive
        self.flatten = flatten

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
                locations.append(current)

        if self.pattern is None:
            [logger.info('Will copy: %s', x) for x in locations]
            self._locations_to_copy = locations
        else:
            tmp_locations = []
            for location in locations:
                logger.info('Will copy "%s" files from: %s', self.pattern, location)
                if self.recursive:
                    files = location.rglob(self.pattern)
                else:
                    files = location.glob(self.pattern)
                tmp_locations.append(files)
            self._locations_to_copy = itertools.chain(*tmp_locations)

    @property
    def locations_to_copy(self):
        new, old = itertools.tee(self._locations_to_copy, 2)
        self._locations_to_copy = old
        return new

    def copy(self, destination):
        """
        Handles copying data to the build location.

        Args:
            destination (str, pathlib.Path): Destination directory.

        """
        destination = Path(destination)
        src_base = str(self.directory)
        if self.flatten:
            dst_base = destination
        else:
            dst_base = Path(destination.joinpath(self.directory.stem))

        for src in self.locations_to_copy:
            if src.is_dir():
                for dir_path, dir_names, file_names in os.walk(str(src)):
                    if self.flatten:
                        dst_dir = dst_base
                    else:
                        dst_dir = Path(dir_path.replace(src_base, str(dst_base)))
                    if not dst_dir.exists():
                        dst_dir.mkdir(parents=True)
                    for file in file_names:
                        shutil.copy2(os.path.join(dir_path, file), str(dst_dir))
            else:
                if self.flatten:
                    dst_dir = dst_base
                else:
                    dst_dir = Path(str(src.parent).replace(src_base, str(dst_base)))
                if not dst_dir.exists():
                    dst_dir.mkdir(parents=True)
                shutil.copy2(str(src), str(dst_dir))


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
        make_zip (bool): Optionally, create a zip file of the build contents.
            Defaults to False.

    """

    def __init__(
        self,
        app_directory,
        package_name,
        supplemental_data=None,
        build_directory=None,
        make_zip=False,
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

        with cd(self.app_directory):
            self._install_dependencies()
            self._handle_supplemental_data()
            self._cleanup_files()
            if self.make_zip:
                self._zip_files()

    @log_entrance_exit
    def _install_dependencies(self):
        """Installs dependencies contained in requirements.txt or setup.py."""

        requirements_file = self.app_directory.joinpath('requirements.txt')

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
        else:
            cmd = [
                sys.executable,
                '-m',
                'pip',
                'install',
                '.',
                '-t',
                str(self.build_directory),
            ]

        logger.debug('Running subprocess cmds: %s', cmd)

        try:
            _ = subprocess.run(cmd, check=True)
        except Exception:
            logger.error('Pip failed to install the app using cmd=[%s].', cmd)
            raise

        if package_copy_required:
            shutil.copytree(
                self.package_dir, self.build_directory.joinpath(self.package_name)
            )

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

        [data.copy(self.build_directory) for data in self.supplemental_data]

    @log_entrance_exit
    def _zip_files(self):
        """Zips files in root build_directory."""

        zip_file = Path(self.build_directory.parent).joinpath(
            self.package_name + '.zip'
        )
        logger.info('Creating zip file: %s', zip_file)

        shutil.make_archive(zip_file.with_suffix(''), 'zip', self.build_directory)
        shutil.move(str(zip_file), self.build_directory)

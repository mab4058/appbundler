"""CLI for appbundler."""

import argparse
import logging
import sys
from pathlib import Path

from appbundler.appbundler import AppBundler, Config
from appbundler.utils import check_path

logger = logging.getLogger()


def main():
    parser = argparse.ArgumentParser(description='Bundle an app.')
    parser.add_argument(
        'config',
        help='Full path to an appBuilder config file. This '
        'must be located in the app\'s root directory.',
    )
    parser.add_argument(
        '--dir', required=False, type=str, help='Override the default built directory.'
    )
    flags = parser.add_argument_group('Flags')
    flags.add_argument(
        '--zip',
        action='store_true',
        default=False,
        required=False,
        help='Create zip file of the build.',
    )
    flags.add_argument(
        '-v',
        action='count',
        required=False,
        help='Add a logger handler to stdout. \'v\' for INFO,' '\'vv\' for DEBUG',
    )

    args = parser.parse_args()

    log_levels = {1: logging.INFO, 2: logging.DEBUG}

    if args.v:
        handler = logging.StreamHandler(stream=sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(log_levels[args.v])
        logger.info('Adding stdout logging handler.')

    # Parse toml config file.
    config = Config(args.config)

    app_path = Path(args.config)
    check_path(app_path)

    if args.dir is not None:
        check_path(args.dir)

    bundler = AppBundler(
        app_path.parent,
        config.package,
        supplemental_data=config.data,
        build_directory=args.dir,
        make_zip=args.zip,
    )
    bundler.bundle()


if __name__ == '__main__':
    main()

import tempfile
from pathlib import Path

from appbundler.appbundler import AppBundler, Config, SupplementalData


def test_config(app_path):
    app_config = app_path / 'appbundler.toml'
    config = Config(app_config)
    assert str(app_config.resolve()) == str(config._file)
    assert config.package == 'myapp'
    assert len(config.data) == 1


def test_supplemental_data(app_path):
    data_path = app_path / 'data'

    test_files = {
        'test': str(data_path / 'test.json'),
        'test2': str(data_path / 'test2.json'),
        'sub': str(data_path / 'sub' / 'sub.json'),
        'sub2': str(data_path / 'sub' / 'sub2.yaml'),
    }

    data = SupplementalData(data_path)
    assert str(data.directory) == str(data_path)
    assert data.sub_directories is None
    locations = list(data.locations_to_copy)
    assert len(locations) == 1
    assert str(locations[0]) == str(data_path)

    data = SupplementalData(data_path, sub_directories=['/sub'])
    assert str(data.directory) == str(data_path)
    assert data.sub_directories == ['/sub']
    locations = list(data.locations_to_copy)
    assert len(locations) == 1
    assert str(locations[0]) == str(data_path / 'sub')

    data = SupplementalData(data_path, pattern='*.json')
    assert str(data.directory) == str(data_path)
    assert data.sub_directories is None
    locations = list(data.locations_to_copy)
    assert len(locations) == 2
    truth = [test_files['test'], test_files['test2']]
    assert all(str(x) in truth for x in locations)

    data = SupplementalData(data_path, sub_directories=['/sub'], pattern='*.json')
    assert str(data.directory) == str(data_path)
    assert data.sub_directories == ['/sub']
    locations = list(data.locations_to_copy)
    assert len(locations) == 1
    assert str(locations[0]) == test_files['sub']

    data = SupplementalData(data_path, pattern='*.yaml', recursive=True)
    assert str(data.directory) == str(data_path)
    assert data.sub_directories is None
    locations = list(data.locations_to_copy)
    assert len(locations) == 1
    assert str(locations[0]) == test_files['sub2']

    with tempfile.TemporaryDirectory() as temp_dir:
        data.copy(temp_dir)
        assert Path(temp_dir).joinpath(test_files['sub2']).exists()

    with tempfile.TemporaryDirectory() as temp_dir:
        data = SupplementalData(data_path, pattern='*.yaml', recursive=True,
                                flatten=True)
        data.copy(temp_dir)
        assert Path(temp_dir).joinpath(Path(test_files['sub2']).name).exists()


def test_appbundler(app_path):
    data_path = app_path / 'data'
    data = SupplementalData(data_path, pattern='*.json', recursive=True)

    with tempfile.TemporaryDirectory() as temp_dir:
        build_dir = Path(temp_dir) / 'build'
        expected_zip = build_dir / 'myapp.zip'
        expected_dep = build_dir / 'toml'
        expected_files = {
            'test': build_dir / 'data/test.json',
            'test2': build_dir / 'data/test2.json',
            'sub': build_dir / 'data/sub/sub.json',
            'sub2': build_dir / 'data/sub/sub2.yaml',
        }
        bundler = AppBundler(
            app_path,
            'myapp',
            supplemental_data=[data],
            build_directory=temp_dir,
            make_zip=True
        )
        bundler.bundle()
        assert expected_zip.exists()
        assert expected_dep.exists()
        assert expected_files['test'].exists()
        assert expected_files['test2'].exists()
        assert expected_files['sub'].exists()
        assert not expected_files['sub2'].exists()

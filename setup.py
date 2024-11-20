#!/usr/bin/env python3
# to install: `pip3 install -e .`
# to install latest from pypi: `pip3 install --upgrade --upgrade-strategy eager --no-cache-dir pheweb`
# to upload to pypi: `./setup.py publish`
# to update deps: `kpa pip-find-updates`, edit, `pip3 install -U --upgrade-strategy=eager .`, test
# to test: `./setup.py test` or `pytest`

from setuptools import setup
import importlib
import sys


if sys.platform.startswith('win'):
    raise Exception("PheWeb doesn't support Windows, because pysam doesn't support windows.")
if sys.version_info.major <= 2:
    print("PheWeb requires Python 3.  Please use Python 3 by installing it with `pip3 install pheweb` or `python3 -m pip install pheweb`.")
    sys.exit(1)
if sys.version_info < (3, 12):
    print("PheWeb requires Python 3.12 or newer.  Use Miniconda or Homebrew or another solution to install a newer Python.")
    sys.exit(1)


def load_module_by_path(module_name, filepath):
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    if not spec: raise Exception(module_name, filepath, spec)
    module = importlib.util.module_from_spec(spec)
    module.__spec__.loader.exec_module(module)
    return module
version = load_module_by_path('preprocessing.version', 'preprocessing/version.py').version


if sys.argv[-1] in ['publish', 'pub']:
    import kpa.pypi_utils
    kpa.pypi_utils.upload_package(version)
    sys.exit(0)


setup(
    name='PheWeb',
    version=version,
    description="A tool for building PheWAS websites from association files",
    long_description='Please see the README `on github <https://github.com/statgen/pheweb>`__',
    author="Peter VandeHaar",
    author_email="pjvh@umich.edu",
    url="https://github.com/statgen/pheweb",
    classifiers=[
        'Programming Language :: Python :: 3 :: Only',
        'Operating System :: Unix',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
    packages=['preprocessing'],
    entry_points={'console_scripts': [
        'pheweb=preprocessing.command_line:main',
        #'detect-ref=pheweb.load.detect_ref:main',
    ]},
    include_package_data=True,
    zip_safe=False,
    cffi_modules=['preprocessing/load/cffi/ffibuilder.py:ffibuilder'],
    python_requires=">=3.12",
    setup_requires=[
        'cffi==1.16.0',
    ],
    install_requires=[
        'Flask==3.0.3',
        'Flask-Compress==1.15',
        'Flask-Login==0.6.3',
        'rauth==0.7.3',
        'pysam==0.22.1',
        'intervaltree==3.1.0',
        'tqdm==4.66.4',
        'scipy==1.13.1',
        'numpy==1.26.4',
        'requests[security]==2.32.3',
        'gunicorn==22.0.0',
        'boltons==24.0.0',
        'cffi==1.16.0', # in both `setup_requires` and `install_requires` as per <https://github.com/pypa/setuptools/issues/391>
        'wget==3.2',
        'gevent==24.2.1',
        'psutil==6.0.0',
        'markupsafe==2.1.5',  # flask 1.1 uses jinja 2.x which breaks with markupsafe>2.0.1.  Pinning all deps might be better.
    ]
)

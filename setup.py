#!/usr/bin/env python3

# to install: `pip3 install -e .`
# to install latest from pypi: `pip3 install --upgrade --upgrade-strategy eager --no-cache-dir pheweb`
# to upload to pypi: `./setup.py publish`
# to update deps: `kpa pip-find-updates`, edit, `pip3 install -U --upgrade-strategy=eager .`, test
# to test: `./setup.py test` or `pytest`

from setuptools import setup
import importlib
import sys


if sys.platform.startswith("win"):
    raise Exception(
        "PheWeb2 doesn't support Windows."
    )
if sys.version_info.major <= 2:
    print(
        "PheWeb2 requires Python 3."
    )
    sys.exit(1)
if sys.version_info < (3, 12):
    print(
        "PheWeb2 requires Python 3.12 or newer."
    )
    sys.exit(1)


def load_module_by_path(module_name, filepath):
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    if not spec:
        raise Exception(module_name, filepath, spec)
    module = importlib.util.module_from_spec(spec)
    module.__spec__.loader.exec_module(module)
    return module


version = load_module_by_path(
    "pheweb_api.version", "pheweb_api/version.py"
).version


if sys.argv[-1] in ["publish", "pub"]:
    import kpa.pypi_utils

    kpa.pypi_utils.upload_package(version)
    sys.exit(0)


setup(
    name = "PheWeb2",
    version = version,
    description = "A data model and API for building PheWeb websites from genome-wide and phenome-wide association files",
    long_description = "Please see the README `on github <https://github.com/GaglianoTaliun-Lab/PheWeb2-API>`__",
    url="https://github.com/GaglianoTaliun-Lab/PheWeb2-API",
    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
        "Operating System :: Unix",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    packages=["pheweb_api"],
    py_modules=["app", "config"],
    entry_points={
        "console_scripts": [
            "pheweb2=pheweb_api.command_line:main"
        ]
    },
    include_package_data=True,
    zip_safe=False,
    cffi_modules=["pheweb_api/load/cffi/ffibuilder.py:ffibuilder"],
    python_requires=">=3.12",
    setup_requires=[
        "cffi==1.16.0",
    ],
    install_requires=[
        "astroid==3.3.5",
        "Flask==3.0.3",
        "Flask-Compress==1.15",
        "Flask-Cors==5.0.0",
        "Flask-Login==0.6.3",
        "flask-restx==1.3.0",
        "Flask-Caching==2.3.1",
        "pytest==8.4.1",
        "gunicorn==22.0.0",
        "psutil==6.0.0",
        "setuptools==75.5.0",
        "tomlkit==0.13.2",
        "zope.event==5.0",
        "rauth==0.7.3",
        "pysam==0.22.1",
        "intervaltree==3.1.0",
        "tqdm==4.66.4",
        "scipy==1.15.1",
        "numpy==2.2.2",
        "requests[security]==2.32.3",
        "boltons==24.0.0",
        "cffi==1.16.0",  # in both `setup_requires` and `install_requires` as per <https://github.com/pypa/setuptools/issues/391>
        "wget==3.2",
        "gevent==24.2.1",
        #"markupsafe==2.1.5",  # flask 1.1 uses jinja 2.x which breaks with markupsafe>2.0.1.  Pinning all deps might be better.
        "python_dotenv==1.0.1",
        "intervaltree==3.1.0",
        "ipython==8.12.3",
        "ordered_set==4.1.0",
        "polars==1.28.1"
    ],
)

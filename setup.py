try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name="sphinx_python_api_utils",
    version="0.1-SNAPSHOT",
    description="Sphinx Utilities for generating API rst files",
    url="https://github.com/SpiNNakerManchester/sphinx_python_api_utils",
    packages=['sphinx_pythons_api_utils']
)

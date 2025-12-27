from setuptools import setup, find_packages
import tomllib
from pathlib import Path

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


# Read metadata from pyproject.toml
def get_version():
    with open("pyproject.toml", "rb") as f:
        pyproject_data = tomllib.load(f)
    return pyproject_data["project"]["version"]


# Static metadata
PROJECT_NAME = "wikigen"
AUTHOR_NAME = "Mithun Ramesh"
DESCRIPTION = "Wiki's for nerds, by nerds"
MIN_PYTHON_VERSION = "3.12"

setup(
    name=PROJECT_NAME,
    version=get_version(),
    author=AUTHOR_NAME,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Software Development :: Documentation",
        "Topic :: Text Processing :: Markup",
    ],
    python_requires=f">={MIN_PYTHON_VERSION}",
    entry_points={
        "console_scripts": [
            "wikigen=wikigen.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)

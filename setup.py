import os
import sys
from pathlib import Path

from setuptools import find_packages, setup

setup(
    name="akira",
    author="eugenepy",
    author_email="tn00372136@gmail.com",
    python_requires='>=3.5',
    packages=find_packages(exclude=['tests', 'tests.*']),
    include_package_data=True,
    zip_safe=False,
    install_requires=['faust'],
)

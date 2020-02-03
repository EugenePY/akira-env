import os
import sys
from pathlib import Path

from setuptools import find_packages, setup

with open(Path(os.path.dirname(__file__))/"requirements.txt", "r") as f:
    requires = [line.strip() for line in f]

setup(
    name="akira-test",
    author="eugenepy",
    author_email="tn00372136@gmail.com",
    python_requires='>=3.5',
    install_requires=requires,
    packages=find_packages(exclude='test'),
    dependency_links=[
        "git+https://github.com/EugenePY/akira-data.git@master#egg=akira-data"],
    )
#!/usr/bin/env python3
"""Setup script for Taidy - Smart linter/formatter with automatic tool detection."""

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Smart linter/formatter with automatic tool detection"

# Read version from package
def get_version():
    version_file = os.path.join(os.path.dirname(__file__), 'taidy', '__init__.py')
    if os.path.exists(version_file):
        with open(version_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('__version__'):
                    return line.split('=')[1].strip().strip('"').strip("'")
    return "0.1.0"

setup(
    name="taidy",
    version=get_version(),
    description="Smart linter/formatter with automatic tool detection",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="singletoned",
    author_email="",
    url="https://github.com/singletoned/taidy",
    packages=find_packages(),
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    keywords="linter formatter python javascript typescript go rust ruby php sql shell css json html markdown",
    entry_points={
        "console_scripts": [
            "taidy=taidy.cli:main",
        ],
    },
    install_requires=[
        # No external dependencies - uses only standard library
    ],
    extras_require={
        "dev": [
            "pytest",
            "black",
            "ruff",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/singletoned/taidy/issues",
        "Source": "https://github.com/singletoned/taidy",
        "Changelog": "https://github.com/singletoned/taidy/blob/main/CHANGELOG.md",
    },
)
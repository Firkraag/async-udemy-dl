#!/usr/bin/env python
# encoding: utf-8
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="async-udemy-dl",
    version="0.1.1",
    author="wq2",
    author_email="smilingwang2@gmail.com",
    description="simple script to asynchronously download udemy course",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Firkraag/async-udemy-dl",
    packages=setuptools.find_packages(),
    py_modules=['async_udemy_dl'],
    python_requires='>=3.7',
    install_requires=['requests', 'aiohttp'],
    entry_points={
        'console_scripts': [
            'async-udemy-dl = async_udemy_dl:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

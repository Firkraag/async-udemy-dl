#!/usr/bin/env python
# encoding: utf-8
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="async-udemy-dl",
    version="0.1.0",
    author="wq2",
    author_email="smilingwang2@gmail.com",
    description="simple script to asynchronously download udemy course",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Firkraag/async-udemy-dl",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

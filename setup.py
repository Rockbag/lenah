#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

requirements = ['chalice', 'pydantic', 'json-merge-patch', 'pynamodb']

test_requirements = ['pytest>=3', ]

setup(
    author="Balint Biro",
    author_email='rockbag123@gmail.com',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Lenah is an opinionated REST framework for Chalice",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n',
    include_package_data=True,
    keywords='lenah',
    name='lenah',
    packages=find_packages(include=['lenah', 'lenah.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/Rockbag/lenah',
    version='0.1.2',
    zip_safe=False,
)

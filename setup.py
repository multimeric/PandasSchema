# Always prefer setuptools over distutils
from setuptools import setup, find_packages
from pathlib import Path

here = Path(__file__).parent

# Get the long description from the README file
with (here / 'README.rst').open() as readme:
    long_description = readme.read()

setup(
    name='PandasSchema',
    version='0.1.0',
    description='A validation library for Pandas data frames using user-friendly schemas',
    long_description=long_description,
    url='https://github.com/pypa/sampleproject',
    author='Michael Milton',
    author_email='michael.r.milton@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3 :: Only'
        'Programming Language :: Python :: 3.5',
    ],

    keywords='pandas csv verification schema',

    packages=find_packages(exclude=['test']),
    install_requires=['numpy', 'pandas'],
)
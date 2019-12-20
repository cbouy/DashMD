from setuptools import setup
from os import path
from codecs import open

here = path.abspath(path.dirname(__file__))

# get version from version.py
__version__ = None
exec(open('dashmd/version.py').read())

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='dashmd',
    version=__version__,
    description='Real time monitoring and visualization of Amber MD simulations',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/cbouy/DashMD',
    author='Cédric Bouysset',
    author_email='bouysset.cedric@gmail.com',
    license='Apache License, Version 2.0',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Operating System :: OS Independent',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Scientific/Engineering :: Chemistry',
        'Topic :: Scientific/Engineering :: Visualization',
    ],
    keywords='science chemistry biology ambermd',
    packages=['dashmd'],
    entry_points = {
        'console_scripts': ['dashmd=dashmd.command_line:main'],
    },
    python_requires='>=3.6',
    install_requires=['numpy>=1.7.1', 'pandas>=0.24.2', 'tornado>=4.3.0', 'pytraj>=2.0.4', 'bokeh>=1.3.4, <1.4.0'],
    project_urls={
        'Bug Reports':  'https://github.com/cbouy/DashMD/issues',
        'Say Thanks!':  'https://saythanks.io/to/cbouy',
    },
    zip_safe=False,
)

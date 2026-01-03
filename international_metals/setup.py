"""
Setup script for Precious Metals Price Tracker
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_file(filename):
    """Read file contents"""
    with open(os.path.join(os.path.dirname(__file__), filename), encoding='utf-8') as f:
        return f.read()

setup(
    name='international-metals-tracker',
    version='2.0.0',
    author='International Metals Tracker Team',
    author_email='contact@example.com',
    description='A Python package for fetching real-time international gold and silver prices',
    long_description=read_file('README.md') if os.path.exists('README.md') else '',
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/international-metals-tracker',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Financial and Insurance Industry',
        'Intended Audience :: Developers',
        'Topic :: Office/Business :: Financial',
        'Topic :: Office/Business :: Financial :: Investment',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    keywords='gold silver price finance precious-metals yahoo-finance msn-money',
    python_requires='>=3.8',
    install_requires=[
        'yfinance>=0.2.28',
        'requests>=2.31.0',
        'pandas>=2.0.0',
        'beautifulsoup4>=4.12.0',
        'lxml>=4.9.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'gold-price=international_metals_pkg.cli:main',
            'silver-price=international_metals_pkg.cli:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
)

# quant_trading/setup.py

from setuptools import setup, find_packages

setup(
    name='quant_trading',
    version='0.1',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'pandas',
        'matplotlib',
        'ta',
        'alpaca-trade-api',
        'ntscraper',
        'vaderSentiment'
    ],
    author='Your Name',
    description='Quant trading bot framework with live and backtest support',
)

# quant_trading/setup.py

from setuptools import setup, find_packages

setup(
    name='quant_trading',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={"": "src"},
    python_requires='>=3.8',
    install_requires=[
        # Core dependencies
        'numpy>=1.20.0',
        'pandas>=1.3.0',
        'pandas_ta>=0.3.14b0',
        'yfinance>=0.1.70',
        'alpaca-py>=0.8.0',
        'ta>=0.10.0',
        'PyYAML>=6.0',
        'python-dotenv>=0.19.0',
        'pytz>=2021.3',
        'requests>=2.26.0',
        'lxml>=4.9.0',
        'html5lib>=1.1',
        
        # Data processing and analysis
        'ntscraper>=0.1.0',
        'vaderSentiment>=3.3.2',
        
        # Backtesting and optimization
        'backtrader>=1.9.76',
        'optuna>=2.10.0',
        'scikit-learn>=1.0.0',
        
        # Visualization
        'matplotlib>=3.5.0',
        'plotly>=5.5.0',
        'dash>=2.0.0',
        
        # Jupyter support
        'jupyter>=1.0.0',
        'notebook>=6.4.0',
        'ipykernel>=6.0.0',
    ],
    extras_require={
        'dev': [
            'pytest>=6.2.5',
            'pytest-cov>=2.12.0',
            'flake8>=4.0.0',
            'black>=22.1.0',
            'mypy>=0.910',
            'sphinx>=4.4.0',
            'sphinx-rtd-theme>=1.0.0',
        ],
    },
    author='Your Name',
    author_email='your.email@example.com',
    description='Quant trading bot framework with live and backtest support',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/quant_trading',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Financial and Insurance Industry',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    keywords='trading, finance, algorithmic trading, backtesting, quantitative finance',
    project_urls={
        'Bug Reports': 'https://github.com/yourusername/quant_trading/issues',
        'Source': 'https://github.com/yourusername/quant_trading',
    },
)

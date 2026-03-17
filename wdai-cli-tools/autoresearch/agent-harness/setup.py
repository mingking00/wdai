from setuptools import setup, find_packages

setup(
    name='cli-anything-wdai-autoresearch',
    version='1.0.0',
    description='CLI interface for wdai_autoresearch - Autonomous research with self-improvement',
    author='wdai',
    packages=find_packages(),
    install_requires=[
        'click>=8.0.0',
    ],
    entry_points={
        'console_scripts': [
            'cli-anything-wdai-autoresearch=cli_anything.autoresearch.cli:cli',
        ],
    },
    python_requires='>=3.10',
)

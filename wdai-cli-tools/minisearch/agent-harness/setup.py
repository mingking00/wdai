from setuptools import setup, find_packages

setup(
    name='cli-anything-wdai-minisearch',
    version='1.0.0',
    description='CLI interface for wdai_minisearch - Semantic search for wdai workspace',
    author='wdai',
    packages=find_packages(),
    install_requires=[
        'click>=8.0.0',
        'sentence-transformers>=2.0.0',
        'chromadb>=0.4.0',
    ],
    entry_points={
        'console_scripts': [
            'cli-anything-wdai-minisearch=cli_anything.minisearch.cli:cli',
        ],
    },
    python_requires='>=3.10',
)

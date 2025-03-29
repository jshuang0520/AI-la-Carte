from setuptools import setup, find_packages

setup(
    name="ai-la-carte",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'geopy>=2.3.0',
        'numpy>=1.24.0',
        'shapely>=2.0.0',
        'pandas>=1.5.0',
        'pyyaml>=6.0.0',
        'requests>=2.28.0'
    ],
    python_requires='>=3.10,<3.11'
) 
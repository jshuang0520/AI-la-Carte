from setuptools import setup, find_packages

# Read requirements from requirements.txt.
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="ai-la-carte",
    version="0.1",
    packages=find_packages(),
    install_requires=requirements,
    python_requires='>=3.10,<3.11'
) 

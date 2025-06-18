from setuptools import find_packages, setup

setup(
    name="tunnel_over_anything",
    version="1.0.0",
    description="a python program for tunneling via various protocols",
    author="androsh7",
    install_requires=[
        "attrs>=25.3.0",
        "loguru>=0.7.3",
        "pypacker>=5.4",
        "toml>=0.10.2",
    ],
    python_requires=">=3.10.12",
)

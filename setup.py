from setuptools import setup

setup(
    name="tunnel_over_anything",
    version="0.1.2",
    description="Tunneling software that disguises TCP/UDP traffic using DNS, HTTP, and other protocols",
    author="androsh7",
    install_requires=[
        "attrs>=25.3.0",
        "loguru>=0.7.3",
        "pypacker>=5.4",
        "toml>=0.10.2",
    ],
    python_requires=">=3.12.0",
)

import setuptools

with open("readme.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="Atomize", 
    version="0.0.1",
    author="Anatoly Melnikov, Vladimir Baikalov",
    author_email="anatoly.melnikov@tomo.nsc.ru",
    description="A modular software for working with scientific devices and combining them into a spectrometer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Anatoly1010/Atomize",
    packages=setuptools.find_packages(),
    license="MIT",
    keywords="liveplot oscilloscope gpib-library experimental-scripts lock-in-amplifier temperature-controller",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
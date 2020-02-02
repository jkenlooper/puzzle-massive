import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="puzzle-massive-api",
    version="0.0.1",
    author="Jake Hickenlooper",
    author_email="jake@weboftomorrow.com",
    description="Puzzle Massive web application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    install_requires=["future",],
    entry_points={
        "console_scripts": [
            "puzzle-massive-api = api.script:main",
            "puzzle-massive-janitor = api.janitor:main",
            "puzzle-massive-worker = api.worker:main",
            "puzzle-massive-artist = api.artist:main",
            "puzzle-massive-scheduler = api.scheduler:main",
            "puzzle-massive-testdata = api.testdata:main",
        ]
    },
)

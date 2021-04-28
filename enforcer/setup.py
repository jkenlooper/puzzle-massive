import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="puzzle-massive-enforcer",
    version="0.0.1",
    author="Jake Hickenlooper",
    author_email="jake@weboftomorrow.com",
    description="Puzzle Massive enforcer app",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    install_requires=[],
    entry_points={
        "console_scripts": ["puzzle-massive-enforcer = enforcer.script:main"]
    },
)

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="salt-docs",
    version="0.1.1",
    author="Mithun Ramesh",
    description="Intelligent codebase analysis and documentation generation tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Software Development :: Documentation",
        "Topic :: Text Processing :: Markup",
    ],
    python_requires=">=3.12",
    entry_points={
        "console_scripts": [
            "salt-docs=salt_docs.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)

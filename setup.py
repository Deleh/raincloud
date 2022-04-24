from setuptools import find_packages, setup

setup(
    name="raincloud",
    long_description=open("README.org").read(),
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=["flask", "toml"],
)

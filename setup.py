from setuptools import setup, find_packages

install_requirements = []
test_requirements = []
docs_requirements = []

setup(
    name="Django Restframework Stripe",
    version="0.1",
    packages=find_packages(exclude=["tests"]),
    install_requires=install_requirements,
    author="Andrew Young",
    author_email="ayoung@thewulf.org",
    license="BSD2",
    description="Restfull endpoints for Django projects with Stripe.",
    tests_require=test_requirements,
    extras_require={"docs": docs_requirements}
    )

from setuptools import setup, find_packages

install_requirements = [
    "Django>=1.8",
    "djangorestframework==3.3.2",
    "Jinja2==2.8",
    "MarkupSafe==0.23",
    "pytz==2015.7",
    "requests==2.9.1",
    "six==1.10.0",
    "stripe==1.28.0",
    ]

test_requirements = [
   "psycopg2==2.6.1",
   "model-mommy==1.2.6",
   "coverage==4.0.3",
   "py==1.4.31",
   "pytest==2.8.5",
   "pytest-cov==2.2.0",
   "pytest-cover==3.0.0",
   "pytest-django==2.9.1",
    ]

docs_requirements = [
   "alabaster==0.7.7",
   "Babel==2.2.0",
   "snowballstemmer==1.2.1",
   "Sphinx==1.3.4",
   "sphinx-rtd-theme==0.1.9",
   "Pygments==2.1",
   "docutils==0.12",
    ]


setup(
    name="Django Restframework Stripe",
    version="1.0",
    packages=find_packages(exclude=["tests"]),
    install_requires=install_requirements,
    author="Andrew Young",
    author_email="ayoung@thewulf.org",
    license="BSD",
    description="Restfull endpoints for Django projects with Stripe.",
    tests_require=test_requirements,
    extras_require={"docs": docs_requirements}
    )


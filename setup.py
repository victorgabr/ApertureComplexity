from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='Complexity',
    version='0.1.0',
    description='Python 3.x port of the Eclipse ESAPI plug-in script',
    long_description=readme,
    author='Victor G. L Alves',
    author_email='victorgabr@gmail.com',
    url='https://github.com/victorgabr/ApertureComplexity',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)

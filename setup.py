from setuptools import setup, find_packages


REQUIRES = [
    'aiohttp==3.2.1',
    'requests==2.18.4',
    'websockets==4.0.1',
]

with open('README.txt') as file:
    long_desc = file.read()

setup(
    name='tastyworks',
    author='Boyan Soubachov',
    author_email='boyanvs@gmail.com',
    url='http://pypi.python.org/pypi/tastyworks/',
    version='0.1.1',
    packages=find_packages(exclude=['main.py']),
    python_requires='>= 3.6.0',
    description='Tastyworks (unofficial) API',
    license='LICENSE.txt',
    long_description=long_desc,
    install_requires=REQUIRES,
    entry_points={
        'console_scripts': ['tasty=tastyworks.example:main']
    },
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache License",
        "Operating System :: OS Independent",
    ),

)

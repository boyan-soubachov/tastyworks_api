from setuptools import setup, find_packages


REQUIRES = [
    'aiohttp==3.2.1',
    'dataclasses',
    'requests==2.18.4',
    'websockets==6.0',
]

TEST_REQUIRES = [
    'pytest'
]

with open('README.md', 'r', encoding='utf8') as file:
    long_desc = file.read()

setup(
    name='tastyworks',
    author='Boyan Soubachov',
    author_email='boyanvs@gmail.com',
    url='http://pypi.python.org/pypi/tastyworks/',
    version='3.1.0',
    packages=find_packages(exclude=['main.py']),
    python_requires='>= 3.6.0',
    description='Tastyworks (unofficial) API',
    license='LICENSE.txt',
    long_description=long_desc,
    long_description_content_type='text/markdown',
    install_requires=REQUIRES,
    extras_require={
        'testing': TEST_REQUIRES,
    },
    keywords=['tastyworks', 'trading', 'api', 'algorithmic'],
    entry_points={
        'console_scripts': ['tasty=tastyworks.example:main']
    },
    classifiers=(
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ),

)

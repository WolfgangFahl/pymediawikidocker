# ! important
# see https://stackoverflow.com/a/27868004/1497139
from setuptools import setup
from collections import OrderedDict

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pymediawikidocker',
    version='0.0.14',

    packages=['mwdocker',],
    
    package_data={
        "mwdocker": ["resources/templates/*"],
    },

    entry_points={
      'console_scripts': [
        'mwcluster = mwdocker.mwcluster:main',   
      ],
    },
    author='Wolfgang Fahl',
    author_email='wf@bitplan.com',
    maintainer='Wolfgang Fahl',
    url='https://github.com/WolfgangFahl/pymediawikidocker',
    project_urls=OrderedDict(
        (
            ("Documentation", "http://wiki.bitplan.com/index.php/Pymediawikidocker"),
            ("Code", "https://github.com/WolfgangFahl/pymediawikidocker"),
            ("Issue tracker", "https://github.com/WolfgangFahl/pymediawikidocker/issues"),
        )
    ),
    license='Apache License',
    description='Python controlled mediawiki docker application cluster installation',
    install_requires=[
          'Jinja2',
          'python-on-whales',
          'six',
          'mysql-connector-python'
    ],
    classifiers=[
            'Programming Language :: Python',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9'
    ],
    long_description=long_description,
    long_description_content_type='text/markdown'
)

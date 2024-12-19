#!/usr/bin/env python

from setuptools import setup

with open('README.md') as f:
    long_description = f.read()

setup(name="target-athena",
      version="0.0.1",
      description="Singer.io target for writing CSV files and uploading to S3 and Athena.",
      long_description=long_description,
      long_description_content_type='text/markdown',
      author="Andrew Stewart",
      url='https://github.com/andrewcstewart/target-athena',
      classifiers=[
          'License :: OSI Approved :: Apache Software License',
          'Programming Language :: Python :: 3 :: Only'
      ],
      py_modules=["target_athena"],
      install_requires=[
          'pipelinewise-singer-python==1.*',
          'singer-sdk==^0.1.0',
          'inflection==0.5.1',
          'boto3==1.35.63',
          'PyAthena==2.2.0',
      ],
      extras_require={
          "test": [
              "nose==1.3.7",
              "pylint==2.7.2"
          ]
      },
      entry_points="""
          [console_scripts]
          target-athena=target_athena:main
       """,
      packages=["target_athena"],
      package_data = {},
      include_package_data=True,
)

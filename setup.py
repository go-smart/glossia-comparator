from setuptools import setup

setup(name='glossia.comparator',
      version='0.1.2',
      packages=['glossia', 'glossia.comparator'],

      description='Go-Smart Simulation Architecture XML interpretation',
      author='Phil Weir (NUMA Engineering Services Ltd.)',
      author_email='phil.weir@numa.ie',
      url='http://gosmart-project.eu/',

      install_requires=[
        'lxml',
        'munkres'
      ],

      scripts=[
          'scripts/go-smart-comparator',
      ])

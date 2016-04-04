from distutils.core import setup

setup(name='glossia.comparator',
      version='0.1',
      packages=['glossia.comparator'],

      description='Go-Smart Simulation Architecture XML interpretation',
      author='NUMA Engineering Services Ltd.',
      author_email='phil.weir@numa.ie',
      url='http://gosmart-project.eu/',

      scripts=[
          'scripts/go-smart-comparator',
      ])

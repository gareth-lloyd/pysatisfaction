import os
from setuptools import setup

init = os.path.join(os.path.dirname(__file__), 'pysatisfaction', '__init__.py')
version_line = [l for l in open(init) if l.startswith('VERSION')][0]
VERSION = eval(version_line.split('=')[-1])

desc = 'Client for Get Satisfaction API'
setup(
	name='pysatisfaction',
	version=VERSION,
	description=desc,
	url='https://github.com/gareth-lloyd/pysatisfaction',
	author='Gareth Lloyd',
	author_email='glloyd@gmail.com',
	packages=['pysatisfaction'],
	classifiers=[
		'Development Status :: 4 - Beta',
		'Environment :: Server Environment',
		'Intended Audience :: Developers',
		'Operating System :: OS Independent',
		'Programming Language :: Python',
		'Topic :: Software Development :: Libraries :: Python Modules',
	],
	long_description=desc,
)

from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in ksa_vat/__init__.py
from ksa_vat import __version__ as version

setup(
	name='ksa_vat',
	version=version,
	description='KSA VAT Management and Reporting',
	author='Havenir Solutions',
	author_email='support@havenir.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)

import os
import re

from setuptools import setup, find_packages


def get_version(*file_paths):
    """
    Extract the version string from the file at the given relative path fragments.
    """
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    version_file = open(filename).read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


VERSION = get_version('iscedxreports', '__init__.py')

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='iscedxreports',
    version=VERSION,
    packages=find_packages(),
    include_package_data=True,
    license='BSD License',  # example license
    description='A Django app to handle edX reporting and other customizations for InterSystems',
    long_description=README,
    url='http://www.appsembler.com/',
    author='Appsembler',
    author_email='opensources@appsembler.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.0',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=[
    ],
    entry_points={
        "openedx.course_tab": [
            "course_feedback = iscedxreports.tabs:CourseFeedbackTab",
        ],
        "lms.djangoapp": [
            "iscedxreports = iscedxreports.apps:ISCEdxReportsConfig",
        ],
        "cms.djangoapp": [
            "iscedxreports = iscedxreports.apps:ISCEdxReportsConfig",
        ]
    },
)

from setuptools import setup, find_packages

setup(
    name='csv2api-router',
    version='0.1.0',
    description='Modular pipeline for processing CSVs and unstructured text to extract API-relevant data.',
    author='Your Name',
    author_email='your.email@example.com',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        # List your project dependencies here
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='django-flexipages',
    version='0.1.0',
    url='https://github.com/dprog-philippe-docourt/django-flexipages',
    license='MIT',
    author='Philippe Docourt',
    author_email='contact@dprog.net',
    description='A minimalist CMS that gives an enhanced alternative to the Django flatpages app.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    include_package_data=True,
    python_requires='>=3.5',
    install_requires=['django'],
    classifiers=[
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Framework :: Django",
        "Development Status :: 5 - Production/Stable",
        "Natural Language :: English"
    ],
    keywords='django cms static pages',
)

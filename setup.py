from setuptools import setup

setup(
    name='pascal',
    version='0.1.0',
    py_modules=['pascal'],
    install_requires=[
        'Click',
        'obspy',
    ],
    entry_points={
        'console_scripts': [
            'pascal = pascal:main',
        ],
    },
)
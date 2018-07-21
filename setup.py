import sys

import setuptools

setup_requires = ['pytest-runner'] if 'test' in sys.argv else []


setuptools.setup(
    name='cloneholio',
    version='0.1.1',
    description='I am cloneholio! I need syncing of my repos.',
    license='MIT',
    author='Andrew Rabert',
    author_email='ar@nullsum.net',
    url='https://gitlab.com/nvllsvm/cloneholio',
    py_modules=['cloneholio'],
    entry_points={'console_scripts': ['cloneholio=cloneholio:main']},
    install_requires=[
        'consumers',
        'gitpython',
        'pygithub',
        'python-gitlab'
    ],
    tests_require=['pytest'],
    setup_requires=setup_requires,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3 :: Only'
    ]
)

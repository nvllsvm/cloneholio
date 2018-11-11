import sys

import setuptools

setup_requires = ['setuptools_scm']

if 'test' in sys.argv:
    setup_requires.append('pytest-runner')


setuptools.setup(
    name='cloneholio',
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
    ],
    python_requires='>=3.6',
    use_scm_version=True
)

import setuptools

setuptools.setup(
    name='cloneholio',
    version='0.7.2',
    description='I am cloneholio! I need syncing of my repos.',
    license='MIT',
    author='Andrew Rabert',
    author_email='ar@nullsum.net',
    url='https://gitlab.com/nvllsvm/cloneholio',
    packages=['cloneholio'],
    entry_points={'console_scripts': ['cloneholio=cloneholio.__main__:main']},
    install_requires=[
        'gitpython',
        'pygithub',
        'python-gitlab'
    ],
    extras_require={
        'test': 'pytest'
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3 :: Only'
    ],
    python_requires='>=3.6'
)

from distutils.core import setup

setup(
    name='kwaras',
    version='2.0',
    packages=['kwaras', 'kwaras.langs', 'kwaras.conf', 'kwaras.formats', 'kwaras.process'],
    package_dir={'kwaras': '',
                 'kwaras.langs': 'src/langs', 'kwaras.conf': 'src/conf',
                 'kwaras.formats': 'src/formats', 'kwaras.process': 'src/process'},
    py_modules=['config', 'lexicon'],
    url='http://github.com/serapio/kwaras',
    license='MIT-LICENSE',
    author='Lucien Carroll',
    author_email='lucien@discurs.us',
    description='Tools for managing ELAN corpus files'
)

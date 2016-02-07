from distutils.core import setup

setup(
    name='kwaras',
    version='2.1.4',
    packages=['kwaras', 'kwaras.langs', 'kwaras.conf', 'kwaras.formats', 'kwaras.process'],
    package_dir={'kwaras': '',
                 'kwaras.langs': 'src/langs', 'kwaras.conf': 'src/conf',
                 'kwaras.formats': 'src/formats', 'kwaras.process': 'src/process'},
    py_modules=['lexicon'],
    package_data={'kwaras': ['web/*.html', 'web/css/*.css', 'web/js/*.js',
                             'web/css/smoothness/*.css', 'web/css/smoothness/images/*.png']},
    data_files=[('', ['convert-lexicon.COMMAND', 'install-macos.COMMAND', 'export-corpus.COMMAND'])],
    url='http://github.com/serapio/kwaras',
    license='MIT-LICENSE',
    author='Lucien Carroll',
    author_email='lucien@discurs.us',
    description='Tools for managing ELAN corpus files'
)

from distutils.core import setup
import os

css_dir = 'web/css'
css_files = [os.path.join(css_dir, f)
             for f in os.listdir(css_dir) if os.path.splitext(f)[1] == '.css']
js_dir = 'web/js'
js_files = [os.path.join(js_dir, f)
            for f in os.listdir(js_dir) if os.path.splitext(f)[1] == '.js']
smoothness_dir = 'web/css/smoothness'
smoothness_files = [os.path.join(smoothness_dir, f)
                    for f in os.listdir(smoothness_dir) if os.path.splitext(f)[1] == '.css']
images_dir = 'web/css/smoothness/images'
image_files = [os.path.join(images_dir, f)
               for f in os.listdir(images_dir) if os.path.splitext(f)[1] == '.png']

setup(
    name='kwaras',
    version='2.2.0_1',
    install_requires=['openpyxl'],
    packages=['kwaras', 'kwaras.langs', 'kwaras.conf', 'kwaras.formats', 'kwaras.process'],
    package_dir={'kwaras': '',
                 'kwaras.langs': 'src/langs', 'kwaras.conf': 'src/conf',
                 'kwaras.formats': 'src/formats', 'kwaras.process': 'src/process'},
    py_modules=['lexicon'],
    data_files=[('', ['convert-lexicon.COMMAND', 'install-macos.COMMAND', 'export-corpus.COMMAND']),
                ('web', ['web/index_wrapper.html']),
                (css_dir, css_files),
                (js_dir, js_files),
                (smoothness_dir, smoothness_files),
                (images_dir, image_files)],
    url='http://github.com/ucsd-field-lab/kwaras',
    license='MIT-LICENSE',
    author='Lucien Carroll',
    author_email='lucien@discurs.us',
    description='Tools for managing ELAN corpus files',
    console=['gui.py'],
    options={"py2exe": {"bundle_files": 3}}
)

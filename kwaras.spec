# -*- mode: python -*-

block_cipher = None
project_root = '.'


a = Analysis(['kwaras/cli.py'],
             pathex=[project_root],
             binaries=[],
             datas=[('web', 'web'), ('kwaras', 'kwaras')],
             hiddenimports=['tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox', 'tkinter.simpledialog', 'openpyxl', 'kwaras', 'kwaras.formats', 'kwaras.process', 'kwaras.formats.lift', 'kwaras.formats.xlsx', 'kwaras.formats.eaf', 'kwaras.formats.utfcsv', 'kwaras.formats.textgrid', 'kwaras.process.liftadd', 'kwaras.process.web', 'kwaras.process.timealign', 'kwaras.process.reparse', 'kwaras.langs', 'kwaras.langs.Raramuri', 'kwaras.langs.Mixtec', 'kwaras.langs.Kumiai', 'kwaras.langs.Gitonga', 'kwaras.langs.Other'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='kwaras',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
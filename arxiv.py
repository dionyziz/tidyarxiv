#!/bin/python
import os, tempfile, glob, shutil, fnmatch
import sys
import subprocess
import re
import tarfile
import datetime
import json

try:
  with open('.arxiv', encoding='utf-8') as f:
    config = json.loads(f.read())
except FileNotFoundError:
  print('No .arxiv file found. Create an .arxiv file in the root of your project.')
  sys.exit(1)

target = 'main'
if 'target' in config:
  target = config['target']
  if not os.path.isfile(f'{target}.tex'):
    print(f'No "{target}.tex" file was found. Check the "target" in your .arxiv file.')
    sys.exit(1)
else:
  if not os.path.isfile('main.tex'):
    print('No "main.tex" file found. Specify a "target" in your .arxiv file.')
    sys.exit(1)
  else:
    print('No "target" specified in .arxiv file. Using "main".')

files = ['**/*.tex', '**/*.sty', '**/*.bib']
if 'files' in config:
  files = config['files']

files_exclude = []
if 'files_exclude' in config:
  files_exclude = config['files_exclude']

import_files_exclude = files_exclude
if 'import_files_exclude' in config:
  import_files_exclude += config['import_files_exclude']

arxiv_files_include = files
if 'arxiv_files_include' in config:
  arxiv_files_include += config['arxiv_files_include']
else:
  arxiv_files_include += ['**/*.bbl']

arxiv_files_exclude = files_exclude
if 'arxiv_files_exclude' in config:
  arxiv_files_exclude += config['arxiv_files_exclude']
else:
  arxiv_files_exclude += ['**/*.bib']

build_command = 'latexmk -pdf %FILE%'
if 'build_command' in config:
  build_command = config['build_command']

build_command = [part.replace('%FILE%', f'{target}.tex') for part in build_command.split(' ')]

def build_file_list(include_globs, exclude_globs):
  files = []
  for include_glob in include_globs:
    files += glob.glob(include_glob, recursive=True)
  files = list(set(files))

  for exclude_glob in exclude_globs:
    files = [f for f in files if not fnmatch.fnmatch(f, exclude_glob)]

  return files

def filter_tex(filepath):
  def filter_comment(line_content):
    return re.sub(r'(^|[^\\])%.*$', '\\1%', line_content)

  with open(filepath, 'r', encoding='utf-8') as f:
    contents = [filter_comment(l) for l in f.readlines()]

  with open(filepath, 'w', encoding='utf-8') as f:
    f.write(''.join(contents))

filter_files = ['**/*.tex', '**/*.sty']
if 'filter_files' in config:
  filter_files = config['filter_files']

filter_files_exclude = []
if 'filter_files_exclude' in config:
  filter_files_exclude = config['filter_files_exclude']

with tempfile.TemporaryDirectory() as tmpdirname:
  print('Importing files')

  files = build_file_list(files, files_exclude)
  filtered_files = set(build_file_list(filter_files, filter_files_exclude))

  for filename in sorted(files):
    if os.path.isdir(filename):
      continue

    print('\tImporting', filename)

    os.makedirs(os.path.join(tmpdirname, os.path.dirname(filename)), exist_ok=True)
    target_file = os.path.join(tmpdirname, filename)
    shutil.copy(filename, target_file)

    if filename in filtered_files:
      print('\t\tFiltering', filename)
      filter_tex(target_file)

  print('Building TeX')

  made = subprocess.run(
    build_command,
    cwd=tmpdirname,
    capture_output=True,
    check=False
  )

  if made.returncode != 0:
    with open('build.log', 'w', encoding='utf-8') as f:
      f.write(made.stdout.decode('utf-8'))

    print('Error building TeX. See build.log for details.')
    sys.exit(1)

  print('TeX built')

  print('Creating .tar file')

  build_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

  with tarfile.open(f'{target}_{build_time}.tar.gz', 'w:gz') as tar:
    files = set()

    arxiv_files = build_file_list(arxiv_files_include, arxiv_files_exclude)

    for filename in sorted(arxiv_files):
      if os.path.isdir(filename):
        continue

      print('\tAdding', filename)
      tar.add(os.path.join(tmpdirname, filename), arcname=filename)

  shutil.copy(os.path.join(tmpdirname, f'{target}.pdf'), f'{target}_{build_time}.pdf')

  print('Tarball created: ', f'{target}_{build_time}.tar.gz')
  print('PDF created: ', f'{target}_{build_time}.pdf')

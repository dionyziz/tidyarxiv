#!/usr/bin/env python

import os, tempfile, glob, shutil, fnmatch
import sys
import subprocess
import re
import tarfile
import datetime
import json

CONFIG_NAME = os.environ.get('TIDYARXIV_CONFIG_NAME', 'tidyarxiv.cfg')

def build_file_list(include_globs, exclude_globs, rootdir=None):
  print('Include globs: ', include_globs)
  print('Exclude globs: ', exclude_globs)

  files = []
  for include_glob in include_globs:
    files += glob.glob(include_glob, root_dir=rootdir, recursive=True)
  files = list(set(files))

  print('Files before exclusion: ', str(sorted(files)))

  for exclude_glob in exclude_globs:
    files = [f for f in files if not fnmatch.fnmatch(f, exclude_glob)]
    print(f'Applying ${exclude_glob}: ', str(sorted(files)))

  print('Files after exclusion: ', str(sorted(files)))

  return files

def filter_tex(filepath):
  def filter_comment(line_content):
    return re.sub(r'(^|[^\\])%.*$', '\\1%', line_content)

  with open(filepath, 'r', encoding='utf-8') as f:
    contents = [filter_comment(l) for l in f.readlines()]

  with open(filepath, 'w', encoding='utf-8') as f:
    f.write(''.join(contents))

def write_build_log(filepath, build_result):
  """Write build log to specified file path"""
  with open(filepath, 'w', encoding='utf-8') as f:
    f.write('STDERR:\n')
    f.write('=======\n')
    f.write(build_result.stderr.decode('utf-8'))
    f.write('\n')
    f.write('STDOUT:\n')
    f.write('=======\n')
    f.write(build_result.stdout.decode('utf-8'))
    f.write('\n')

def main():
  try:
    with open(CONFIG_NAME, encoding='utf-8') as f:
      config = json.loads(f.read())
  except FileNotFoundError:
    print(f'No "{CONFIG_NAME}" file found. Create a "{CONFIG_NAME}" file in the root of your project.')
    sys.exit(1)

  target = 'main'
  if 'target' in config:
    target = config['target']
    if not os.path.isfile(f'{target}.tex'):
      print(f'No "{target}.tex" file was found. Check the "target" in your "{CONFIG_NAME}" file.')
      sys.exit(1)
  else:
    if not os.path.isfile('main.tex'):
      print(f'No "main.tex" file found. Specify a "target" in your "{CONFIG_NAME}" file.')
      sys.exit(1)
    else:
      print(f'No "target" specified in "{CONFIG_NAME}" file. Using "main".')
  
  outdir = config.get('outdir', '.')
  if not os.path.isdir(outdir):
    print(f'Output directory "{outdir}" not found. Check the "outdir" in your "{CONFIG_NAME}" file.')
    sys.exit(1)

  files = ['**/*.tex', '**/*.sty', '**/*.bib']
  if 'files' in config:
    files = config['files']

  files_exclude = []
  if 'files_exclude' in config:
    files_exclude = config['files_exclude']

  import_files_exclude = list(files_exclude)
  if 'import_files_exclude' in config:
    import_files_exclude += config['import_files_exclude']

  arxiv_files_include = list(files)
  if 'arxiv_files_include' in config:
    arxiv_files_include += config['arxiv_files_include']
  else:
    arxiv_files_include += ['**/*.bbl']

  arxiv_files_exclude = list(files_exclude)
  if 'arxiv_files_exclude' in config:
    arxiv_files_exclude += config['arxiv_files_exclude']
  else:
    arxiv_files_exclude += ['**/*.bib']

  build_command = 'latexmk -pdf %FILE%'
  if 'build_command' in config:
    build_command = config['build_command']

  build_command = [part.replace(r'%FILE%', f'{target}.tex') for part in build_command.split(' ')]

  filter_files = ['**/*.tex', '**/*.sty']
  if 'filter_files' in config:
    filter_files = config['filter_files']

  filter_files_exclude = []
  if 'filter_files_exclude' in config:
    filter_files_exclude = config['filter_files_exclude']

  with tempfile.TemporaryDirectory() as tmpdirname:
    print('Importing files')

    import_files = build_file_list(files, files_exclude)

    filtered_files = set(build_file_list(filter_files, filter_files_exclude))

    for filename in sorted(import_files):
      if os.path.isdir(filename):
        continue

      os.makedirs(os.path.join(tmpdirname, os.path.dirname(filename)), exist_ok=True)
      target_file = os.path.join(tmpdirname, filename)
      shutil.copy(filename, target_file)

      print('\tImporting', filename)
      print('\t\tto', target_file)

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
      write_build_log(os.path.join(outdir, 'build.log'), made)
      print('Error building TeX. See build.log for details.')
      sys.exit(1)

    print('TeX built')

    print('Creating .tar file')

    build_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

    with tarfile.open(os.path.join(outdir, f'{target}_{build_time}.tar.gz'), 'w:gz') as tar:
      arxiv_files = build_file_list(arxiv_files_include, arxiv_files_exclude, rootdir=tmpdirname)

      for filename in sorted(arxiv_files):
        if os.path.isdir(filename):
          continue

        print('\tAdding', filename)
        tar.add(os.path.join(tmpdirname, filename), arcname=filename)

    shutil.copy(os.path.join(tmpdirname, f'{target}.pdf'), os.path.join(outdir, f'{target}_{build_time}.pdf'))

    write_build_log(os.path.join(outdir, f'{target}_{build_time}.log'), made)

    # Copy metadata file if specified in config
    if 'metadata_file' in config:
      metadata_file = config['metadata_file']
      if os.path.isfile(metadata_file):
        shutil.copy(metadata_file, os.path.join(outdir, f'{target}_{build_time}.txt'))
        print('Metadata file copied: ', os.path.join(outdir, f'{target}_{build_time}.txt'))
      else:
        print(f'Warning: Metadata file "{metadata_file}" not found. Skipping metadata file copy.')

    print('Tarball created: ', os.path.join(outdir, f'{target}_{build_time}.tar.gz'))
    print('PDF created: ', os.path.join(outdir, f'{target}_{build_time}.pdf'))
    print('Build log saved: ', os.path.join(outdir, f'{target}_{build_time}.log'))

if __name__ == '__main__':
  main()

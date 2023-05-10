A simple script to prepare your LaTeX paper for arXiv submission.

# Description

`tidyarxiv` is a tiny script to run before publishing your paper on arXiv.

First, you create a `tidyarxiv.cfg` configuration file within your project directory.
Then you run `tidyarxiv` on the root of your project directory.

`tidyarxiv` first copies over *only* the files you specify into a separate
temporary *staging* directory (first creating a list of all the files
you choose to *include*, and then excluding all the files you choose
to *exclude*, if any). It *filters* those files by removing unwanted
TeX comments from the relevant files (typically .tex and .sty).

Next, it builds your project within the staging directory to produce your
final PDF file. Among the present files in the staging directory after
the build, it keeps only the ones you choose to include in your final
arxiv. Finally, it produces a .pdf and .tar.gz ready for submission
to [arXiv](https://arxiv.org/).

# Installing

Install using pip:

```
pip install tidyarxiv
```

# Requirements

Python 3.10+

# Config

Create a `tidyarxiv.cfg` file in the root of your project. See
[the example](https://github.com/dionyziz/arxiv/blob/main/arxiv.example).
You can just copy over the example configuration, which has sane defaults.

The file should be a JSON file, which is a dictionary with the following
configuration keys:

* **target**: Optional. Specifies the root .tex file of your project
  (not including the .tex extension). If skipped, "main" is used.
* **files**: Optional. Array of [glob file patterns](https://docs.python.org/3/library/glob.html#module-glob)
  necessary to build your project. By default, all .tex, .sty., and .bib
  files are included.
* **files_exclude**: Optional. Array of [glob file patterns](https://docs.python.org/3/library/glob.html#module-glob)
  to exclude from the build process of your project. By default, no files
  are excluded.
* **arxiv_files_include**: Optional. Array of
  [glob file patterns](https://docs.python.org/3/library/glob.html#module-glob)
  of *additional* files, in addition to *files*, to include in the tarball after your project
  has been built. Note that not all output files of the build process are included by default,
  just files listed in *files*! By default, this includes all .bbl files.
* **arxiv_files_exclude**: Optional. Array of
  [glob file patterns](https://docs.python.org/3/library/glob.html#module-glob)
  of files to exclude from the tarball after your project has been built.
  By default, this include all .bib files.
* **filter_files**: Optional. Array of
  [glob file patterns](https://docs.python.org/3/library/glob.html#module-glob)
  of files to filter for TeX comments.
  By default, this includes all .tex and .sty files.
* **filter_files_exclude**: Optional. Array of
  [glob file patterns](https://docs.python.org/3/library/glob.html#module-glob)
  of files to exclude from TeX filtering.
  Empty by default.
* **build_command**: Optional. A string specifying how to build your project.
  Any occurence of %FILE% within the build command will be replaced by
  your target .tex filename. The default command is "latexmk -pdf %FILE%".

# Running

After installing and configuring, run in the root of your project directory:

```
tidyarxiv
```

# Features

* Includes only the files you want, and excludes the files you don't want.
* Removes LaTeX comments (anything after a "%", nothing more complex).
* Gets rid of .bib files from the final tarball.
* Configurable.
* Sane configuration defaults.

# Authors
Dionysis Zindros and Joachim Neu, Stanford University

# License
GPL v3

# Alternatives
See also the more complex [arxiv-latex-cleaner](https://github.com/google-research/arxiv-latex-cleaner).

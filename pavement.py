from paver.easy import *            # noqa
from paver import doctools          # noqa
from paver.setuputils import setup  # noqa

options(
        sphinx=Bunch(builddir=".build"),
)


def sphinx_builddir(options):
    return path("docs") / options.sphinx.builddir / "html"


@task
def clean_docs(options):
    sphinx_builddir(options).rmtree()


@task
@needs("clean_docs", "paver.doctools.html")
def html(options):
    destdir = path("Documentation")
    destdir.rmtree()
    builtdocs = sphinx_builddir(options)
    builtdocs.move(destdir)


@task
@needs("paver.doctools.html")
def qhtml(options):
    destdir = path("Documentation")
    builtdocs = sphinx_builddir(options)
    sh("rsync -az %s/ %s" % (builtdocs, destdir))


@task
@needs("clean_docs", "paver.doctools.html")
def ghdocs(options):
    builtdocs = sphinx_builddir(options)
    sh("sphinx-to-github", cwd=builtdocs)
    sh("git checkout gh-pages && \
            cp -r %s/* .    && \
            git commit . -m 'Rendered documentation for Github Pages.' && \
            git push origin gh-pages && \
            git checkout master" % builtdocs)


@task
@needs("clean_docs", "paver.doctools.html")
def upload_pypi_docs(options):
    builtdocs = path("docs") / options.builddir / "html"
    sh("python setup.py upload_sphinx --upload-dir='%s'" % (builtdocs))


@task
@needs("upload_pypi_docs", "ghdocs")
def upload_docs(options):
    pass


@task
def autodoc(options):
    sh("contrib/release/doc4allmods djcelery")


@task
def verifyindex(options):
    sh("contrib/release/verify-reference-index.sh")


@task
def flakes(options):
    sh("find djcelery -name '*.py' | xargs pyflakes")


@task
def clean_readme(options):
    path("README").unlink()
    path("README.rst").unlink()


@task
@needs("clean_readme")
def readme(options):
    sh("python contrib/release/sphinx-to-rst.py docs/introduction.rst \
            > README.rst")
    sh("ln -sf README.rst README")


@task
def bump(options):
    sh("bump -c djcelery")


@task
@cmdopts([
    ("coverage", "c", "Enable coverage"),
    ("quick", "q", "Quick test"),
    ("verbose", "V", "Make more noise"),
])
def test(options):
    sh("python setup.py test")


@task
@cmdopts([
    ("noerror", "E", "Ignore errors"),
])
def flake8(options):
    noerror = getattr(options, "noerror", False)
    complexity = getattr(options, "complexity", 22)
    sh("""flake8 . | perl -mstrict -mwarnings -nle'
        my $ignore = m/too complex \((\d+)\)/ && $1 le %s;
        if (! $ignore) { print STDERR; our $FOUND_FLAKE = 1 }
    }{exit $FOUND_FLAKE;
        '""" % (complexity, ), ignore_error=noerror)


@task
@cmdopts([
    ("noerror", "E", "Ignore errors"),
])
def pep8(options):
    noerror = getattr(options, "noerror", False)
    return sh("""find . -name "*.py" | xargs pep8 | perl -nle'\
            print; $a=1 if $_}{exit($a)'""", ignore_error=noerror)


@task
def removepyc(options):
    sh("find . -name '*.pyc' | xargs rm")


@task
@needs("removepyc")
def gitclean(options):
    sh("git clean -xdn")


@task
@needs("removepyc")
def gitcleanforce(options):
    sh("git clean -xdf")


@task
@needs("flake8", "autodoc", "verifyindex", "test", "gitclean")
def releaseok(options):
    pass


@task
@needs("releaseok", "removepyc", "upload_docs")
def release(options):
    pass

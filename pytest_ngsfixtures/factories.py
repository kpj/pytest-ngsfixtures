# -*- coding: utf-8 -*-
import os
import re
import logging
import itertools
import pytest
from pytest_ngsfixtures.os import safe_symlink, safe_copy, safe_mktemp
from pytest_ngsfixtures.layout import setup_sample_layout, setup_reference_layout
from pytest_ngsfixtures.file import setup_fileset, setup_filetype


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_config(request):
    """Return a dictionary with config options."""
    config = {}
    options = [
        'size',
    ]
    for option in options:
        option_name = 'ngs_' + option
        if request is not None:
            conf = request.config.getoption(option_name) or \
                request.config.getini(option_name)
        else:
            conf = None
        config[option] = conf
    return config


def sample_layout(
        runfmt="{SM}",
        layout=None,
        sample_prefix="s",
        use_short_sample_names=True,
        dirname=None,
        sampleinfo=True,
        combinator=itertools.zip_longest,
        sample_aliases=[],
        samples=[None],
        platform_units=[None],
        batches=[None],
        populations=[None],
        paired_end=[True],
        copy=False,
        **kwargs
):
    """Fixture factory for pytest-ngsfixtures sample layouts.

    Generates a directory structure by linking to data files in
    pytest-ngsfixtures data directory. A certain amount of generality
    is allowed in that platform units and batches can be named at
    will. Short sample names can also be used.

    Briefly, sample file names are generated by combining labels in
    the lists **samples** (SM), **platform_units** (PU), **batches**
    (BATCH), and **populations** (POP), and formatting the directory
    structure following the *runfmt* format specification. For
    instance, with samples = ["CHR.HG00512"], populations=None,
    batches=None, platform_units=["010101_AAABBB11XX"], and
    runfmt="{SM}/{PU}/{SM}_{PU}", input files will be organized as
    "CHR.HG00512/010101_AAABBB11XX/CHR.HG00512_010101_AAABBB11XX_1.fastq.gz"
    and similarly for the second read.

    Example:

    .. code-block:: python

       from pytest_ngsfixtures import factories
       my_layout = factories.sample_layout(
           dirname="foo",
           samples=["CHR.HG00512"],
           platform_units=["010101_AAABBB11XX"],
           populations=["CHR"],
           batches=["batch1"],
           runfmt="{POP}/{SM}/{BATCH}/{PU}/{SM}_{PU}",
       )


    Args:
      runfmt (str): run format string
      layout (str): layout label
      sample_prefix (str): sample prefix for short names
      use_short_sample_names (bool): use short sample names
      dirname (str): data directory name
      sampleinfo (bool): create sampleinfo file
      combinator (fun): function to combine sample, platform unit, batch, population labels
      sample_aliases (list): list of sample alias names
      samples (list): list of sample names
      platform_units (list): list of platform units
      batches (list): list of batch (project) names
      populations (list): list of population names
      paired_end (list): list of booleans indicating if a sample run is paired end (True) or single end (False)
      copy (bool): copy fixtures instead of symlinking

    Returns:
      p (py.path.local): tmp directory with sample layout setup

    """
    if len(sample_aliases) > 0:
        assert len(sample_aliases) == len(samples), "length of sample_aliases ({}) and samples ({}) must be equal".format(len(sample_aliases), len(samples))

    @pytest.fixture(autouse=False)
    def sample_layout_fixture(request, tmpdir_factory):
        """Sample layout fixture. Setup sequence input files according to a
        specified sample organization"""
        config = get_config(request)
        kwargs.update(config)
        kwargs['layout'] = layout
        kwargs['alias'] = sample_aliases
        kwargs['sample'] = samples
        kwargs['population'] = populations
        kwargs['platform_unit'] = platform_units
        kwargs['batch'] = batches
        kwargs['copy'] = copy
        kwargs['sampleinfo'] = sampleinfo
        kwargs['runfmt'] = runfmt
        kwargs['paired_end'] = paired_end
        kwargs['use_short_sample_names'] = use_short_sample_names
        path = safe_mktemp(tmpdir_factory, dirname, **kwargs)
        path = setup_sample_layout(path, **kwargs)

        # Alternatively print as debug
        if request.config.option.ngs_show_fixture:
            logger.info("sample_layout")
            logger.info("-------------")
            for x in sorted(path.visit()):
                logger.info(str(x))
        return path
    return sample_layout_fixture


def reference_layout(label="ref", dirname="ref", copy=False, **kwargs):
    """
    Fixture factory for reference layouts.

    Args:
      label (str): ref or scaffolds layout
      dirname (str): reference directory name
      copy (bool): copy file fixture instead of symlinking
      kwargs (dict): keyword arguments


    """
    @pytest.fixture(scope=kwargs.get("scope", "session"), autouse=kwargs.get("autouse", False))
    def reference_layout_fixture(request, tmpdir_factory):
        """Reference layout fixture. Setup the one-chromosome reference files
        or scaffold reference files in a separate directory"""
        path = safe_mktemp(tmpdir_factory, dirname, **kwargs)
        path = setup_reference_layout(path, label=label, **kwargs)
        if request.config.option.ngs_show_fixture:
            logger.info("'{}' reference layout".format(label))
            logger.info("------------------------------------")
            for x in sorted(path.visit()):
                logger.info(str(x))
        return path
    return reference_layout_fixture


def filetype(src, dst=None, fdir=None, rename=False, outprefix="test",
             inprefix=['PUR.HG00731', 'PUR.HG00733'], copy=False,
             **kwargs):
    """Fixture factory for file types. This factory is atomic in that it
    generates one fixture for one file.

    This factory function can be used to generate a named fixtures based
    on a file that then can be used in a test. The test file can be
    renamed for the test by supplying a destination name.

    If the source file is given as a relative path, the function will
    look for existing files in the data directory of the
    pytest_ngsfixtures installation. In order to use a local source
    file use absolute path names.

    Example:

      .. code-block:: python

         from pytest_ngsfixtures import factories
         bamfile = '/path/to/foo.bam'
         bam = factories.filetype(src=bamfile, fdir="bam",
                                  scope="function")

         def test_bam(bam):
             # Do something with bam files


    Args:
      src (str): fixture file name source
      dst (str): fixture file name destination; link name
      fdir (str): fixture output directory
      rename (bool): rename fixture links
      outprefix (str): output prefix
      inprefix (list): list of input prefixes to substitute
      copy (bool): copy fixture file instead of symlinking
      kwargs (dict): keyword arguments

    """
    dst = os.path.basename(src) if dst is None else dst
    if rename:
        pat = "(" + "|".join(inprefix) + ")"
        dst = re.sub(pat, outprefix, dst)

    @pytest.fixture(scope=kwargs.get("scope", "function"), autouse=kwargs.get("autouse", False))
    def filetype_fixture(request, tmpdir_factory):
        """Filetype fixture"""
        p = safe_mktemp(tmpdir_factory, fdir, **kwargs)
        p = setup_filetype(path=p, src=src, dst=dst, setup=True, **kwargs)
        if request.config.option.ngs_show_fixture:
            logger.info("filetype fixture content")
            logger.info("------------------------")
            logger.info(str(p))
        return p
    return filetype_fixture


def fileset(src, dst=None, fdir=None, copy=False, **kwargs):
    """Fixture factory to generate a *named* fileset fixture.

    This factory function can be used to generate a named fileset
    fixture based on a set of files that then can be used in a test.
    The test files can be renamed for the test by supplying a list of
    destination names.

    Note that the fileset fixture factory does not look for files in
    the pytest_ngsfixtures installation directory.

    Example:

      .. code-block:: python

         from pytest_ngsfixtures import factories
         bamfiles = ['foo.bam', 'bar.bam']
         bamset = factories.fileset(src=bamfiles, fdir="bamset",
                                    scope="function")

         def test_bamset(bamset):
             # Do something with bam files

    Args:
      src (list): list of sources
      dst (list): list of destination; if None, use src basename
      fdir (:obj:`str` or :obj:`py._path.local.LocalPath`): output directory
      copy (bool): copy fixture file instead of symlinking
      kwargs (dict): keyword arguments

    Returns:
      func: a fixture function

    """
    assert isinstance(src, list), "not a list"
    assert dst is None or isinstance(dst, list), "not a list"
    if dst is None:
        dst = [None]

    @pytest.fixture(scope=kwargs.get("scope", "function"), autouse=kwargs.get("autouse", False))
    def fileset_fixture(request, tmpdir_factory):
        """Fileset factory

        Setup a set of files

        Args:
          request (FixtureRequest): fixture request object
          tmpdir_factory (py.path.local): fixture request object

        Returns:
          :obj:`py._path.local.LocalPath`: output directory in which the files reside
        """
        p = safe_mktemp(tmpdir_factory, fdir, **kwargs)
        p = setup_fileset(path=p, src=src, dst=dst)
        if request.config.option.ngs_show_fixture:
            logger.info("fileset fixture content")
            logger.info("-----------------------")
            for x in sorted(p.visit()):
                logger.info(str(x))
        return p
    return fileset_fixture


def application_output(application, command, version, end="se", **kwargs):
    """Fixture factory to generate a named application output.

    Args:
      application (str): application name
      command (str): application command name
      version (str): application version
      end (str): paired end or single end

    Returns:
      func: a filetype fixture function

    Example:

      This factory function can be used to generate named application
      outputs that then can be used in a test.

      .. code-block:: python

        from pytest_ngsfixtures import factories
        flagstat = factories.application_output("samtools", "samtools_flagstat", "1.2")

        def test_flagstat(flagstat):
            assert flagstat.exists()

    """
    from pytest_ngsfixtures.config import application_config
    conf = application_config()
    assert application in conf.keys(), "no such application '{}'".format(application)
    assert command in conf[application].keys(), "no such command '{}'".format(command)
    assert type(version) is str, "version must be string"
    if "_versions" in conf[application][command].keys():
        _versions = [str(x) for x in conf[application][command]["_versions"]]
    else:
        _versions = [str(x) for x in conf[application]["_versions"]]
    assert version in _versions, "no such application output for version '{}', application '{}'".format(version, application)
    assert end in ["se", "pe"], "end must be either se or pe"
    params = {'version': version, 'end': end}
    output = [x.format(**params) for x in conf[application][command]['output'].values()]
    if len(output) == 1:
        src = os.path.join("applications", application, output[0])
        return filetype(src, **kwargs)
    else:
        src = [os.path.join("applications", application, x) for x in output]
        return fileset(src, **kwargs)

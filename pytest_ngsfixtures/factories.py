# -*- coding: utf-8 -*-
import os
import re
import logging
import itertools
import pytest
from pytest_ngsfixtures.os import safe_mktemp
from pytest_ngsfixtures.layout import setup_sample_layout, setup_reference_layout
from pytest_ngsfixtures.file import setup_fileset, setup_filetype, ApplicationOutputFixture


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def sample_layout(
        runfmt="{SM}",
        layout=None,
        prefix="s",
        short_name=True,
        dirname=None,
        sampleinfo=True,
        combinator=itertools.zip_longest,
        alias=[],
        sample=[None],
        platform_unit=[None],
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
    the lists **sample** (SM), **platform_unit** (PU), **batches**
    (BATCH), and **populations** (POP), and formatting the directory
    structure following the *runfmt* format specification. For
    instance, with sample = ["CHR.HG00512"], populations=None,
    batches=None, platform_unit=["010101_AAABBB11XX"], and
    runfmt="{SM}/{PU}/{SM}_{PU}", input files will be organized as
    "CHR.HG00512/010101_AAABBB11XX/CHR.HG00512_010101_AAABBB11XX_1.fastq.gz"
    and similarly for the second read.

    Example:

    .. code-block:: python

       from pytest_ngsfixtures import factories
       my_layout = factories.sample_layout(
           dirname="foo",
           sample=["CHR.HG00512"],
           platform_unit=["010101_AAABBB11XX"],
           populations=["CHR"],
           batches=["batch1"],
           runfmt="{POP}/{SM}/{BATCH}/{PU}/{SM}_{PU}",
       )


    Args:
      runfmt (str): run format string
      layout (str): layout label
      prefix (str): sample prefix for short names
      short_name (bool): use short sample names
      dirname (str): data directory name
      sampleinfo (bool): create sampleinfo file
      combinator (fun): function to combine sample, platform unit, batch, population labels
      alias (list): list of sample alias names
      sample (list): list of sample names
      platform_unit (list): list of platform units
      batches (list): list of batch (project) names
      populations (list): list of population names
      paired_end (list): list of booleans indicating if a sample run is paired end (True) or single end (False)
      copy (bool): copy fixtures instead of symlinking

    Returns:
      p (py.path.local): tmp directory with sample layout setup

    """
    if len(alias) > 0:
        assert len(alias) == len(sample), "length of alias ({}) and samples ({}) must be equal".format(len(alias), len(sample))

    @pytest.fixture(autouse=False)
    def sample_layout_fixture(request, tmpdir_factory):
        """Sample layout fixture. Setup sequence input files according to a
        specified sample organization"""
        kwargs['size'] = kwargs.get("size", "tiny")
        if request is not None:
            kwargs['size'] = request.config.getoption("ngs_size")
        kwargs['layout'] = layout
        kwargs['runfmt'] = runfmt
        kwargs['alias'] = alias
        kwargs['sample'] = sample
        kwargs['population'] = populations
        kwargs['platform_unit'] = platform_unit
        kwargs['batch'] = batches
        kwargs['copy'] = copy
        kwargs['sampleinfo'] = sampleinfo
        kwargs['paired_end'] = paired_end
        kwargs['short_name'] = short_name
        path = safe_mktemp(tmpdir_factory, dirname, **kwargs)
        path = setup_sample_layout(path, **kwargs)

        # Alternatively print as debug
        if request.config.option.ngs_show_fixture:
            logger.info("-------------")
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
            logger.info("------------------------------------")
            logger.info("'{}' reference layout".format(label))
            logger.info("------------------------------------")
            for x in sorted(path.visit()):
                logger.info(str(x))
        return path
    return reference_layout_fixture


def filetype(path, src=None, fdir=None, copy=False, **kwargs):
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

         import os
         from pytest_ngsfixtures import factories
         bamfile = '/path/to/foo.bam'
         bam = factories.filetype('foolink.bam', src=bamfile,
                                  fdir="bam",
                                  scope="function")

         def test_bam(bam):
             # Do something with bam files


    Args:
      path (str, py._path.local.LocalPath): fixture path destination; either a full path or a link name
      src (str, py._path.local.LocalPath): fixture file name source. If relative path try to use source file from pytest_ngsfixtures application data. If empty, use basename
      fdir (str, py._path.local.LocalPath): fixture output directory; either a full path, or relative to current tmpdir
      copy (bool): copy fixture file instead of symlinking
      kwargs (dict): keyword arguments

    """
    @pytest.fixture(scope=kwargs.get("scope", "function"), autouse=kwargs.get("autouse", False))
    def filetype_fixture(request, tmpdir_factory):
        """Filetype fixture"""
        p = safe_mktemp(tmpdir_factory, fdir, **kwargs)
        p = p.join(path)
        p = setup_filetype(path=p, src=src, setup=True, **kwargs)
        if request.config.option.ngs_show_fixture:
            logger.info("------------------------")
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
            logger.info("-----------------------")
            logger.info("fileset fixture content")
            logger.info("-----------------------")
            for x in sorted(p.visit()):
                logger.info(str(x))
        return p
    return fileset_fixture


def application_output(application, command, version, end="pe",
                       fdir=None, **kwargs):
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

    @pytest.fixture
    def application_output_fixture(request, tmpdir_factory):
        p = safe_mktemp(tmpdir_factory, fdir, **kwargs)
        ao = ApplicationOutputFixture(application, command, version, end=end, path=p, setup=True)
        if request.config.option.ngs_show_fixture:
            logger.info("----------------------------------")
            logger.info("application output fixture content")
            logger.info("----------------------------------")
            for x in sorted(ao.visit()):
                logger.info(str(x))
        return ao
    return application_output_fixture

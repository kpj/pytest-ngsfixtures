#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_pytest_factories
----------------------------------

Tests for `pytest_ngsfixtures.factories` module.
"""
import os
import re
import py
import pytest
from pytest_ngsfixtures import factories, ROOT_DIR
from pytest_ngsfixtures.config import application_fixtures

DATADIR = os.path.realpath(os.path.join(ROOT_DIR, "data", "tiny"))
for path, dirs, files in os.walk(DATADIR):
    filelist = sorted([os.path.join(DATADIR, x) for x in files])


# Filetypes
bamfile_realpath = os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir, "pytest_ngsfixtures", "data", "applications", "pe", "PUR.HG00731.tiny.bam"))
PURHG00731 = os.path.join("applications", "pe", "PUR.HG00731.tiny.bam")
PURHG00733 = os.path.join("applications", "pe", "PUR.HG00733.tiny.bam")
PURFILES = [PURHG00731, PURHG00733]
bamfile = PURHG00731
bam = factories.filetype(bamfile, fdir="bamfoo", scope="function", numbered=True)
bam_copy = factories.filetype(bamfile, fdir="bamfoo", scope="function", numbered=True, copy=True)
renamebam = factories.filetype(bamfile, fdir="renamebamfoo", rename=True, outprefix="s", scope="function", numbered=True)
renamebam_copy = factories.filetype(bamfile, fdir="renamebamfoo", rename=True, outprefix="s", scope="function", numbered=True)


def test_wrong_sample():
    with pytest.raises(factories.SampleException):
        factories.sample_layout(samples=["foo", "bar"])(None, None)


def test_bam(bam):
    assert not re.search("bamfoo\d+/PUR.HG00731.tiny.bam", str(bam)) is None
    assert bam.realpath() == bamfile_realpath
    assert bam.realpath().exists()


def test_copy_bam(bam_copy):
    assert not re.search("bamfoo\d+/PUR.HG00731.tiny.bam", str(bam_copy)) is None
    assert bam_copy.computehash() == py.path.local(bamfile_realpath).computehash()
    assert bam_copy.realpath().exists()


def test_bam_rename(renamebam):
    assert not re.search("renamebamfoo\d+/s.tiny.bam", str(renamebam)) is None
    assert renamebam.realpath() == bamfile_realpath
    assert renamebam.realpath().exists()


def test_copy_bam_rename(renamebam_copy):
    assert not re.search("renamebamfoo\d+/s.tiny.bam", str(renamebam_copy)) is None
    assert renamebam_copy.computehash() == py.path.local(bamfile_realpath).computehash()
    assert renamebam_copy.realpath().exists()


@pytest.fixture(scope="function")
def combinedbam(tmpdir_factory, bam, renamebam):
    p = tmpdir_factory.mktemp("combined")
    p.join(bam.basename).mksymlinkto(bam.realpath())
    p.join(renamebam.basename).mksymlinkto(renamebam.realpath())
    return p


def test_combine_fixtures(combinedbam):
    flist = sorted([x for x in combinedbam.visit()])
    assert len(flist) == 2
    assert flist[0].dirname == flist[1].dirname
    flist = sorted([x.basename for x in combinedbam.visit()])
    assert flist == ['PUR.HG00731.tiny.bam', 's.tiny.bam']
    fset = set([str(x.realpath()) for x in combinedbam.visit()])
    assert fset == set([bamfile_realpath])


custom_samples = factories.sample_layout(
    dirname="foo",
    samples=["CHS.HG00512", "YRI.NA19238"],
    platform_units=['bar', 'foobar'],
    paired_end=[True, False],
    use_short_sample_names=False,
    runfmt="{SM}/{SM}_{PU}",
    numbered=False,
    scope="function",
)


def test_custom(custom_samples, ref):
    assert custom_samples.basename == "foo"
    flist = [str(x.basename) for x in custom_samples.visit()]
    assert "CHS.HG00512_bar_1.fastq.gz" in flist
    assert "CHS.HG00512_bar_2.fastq.gz" in flist
    assert "YRI.NA19238_foobar_1.fastq.gz" in flist
    assert "YRI.NA19238_foobar_2.fastq.gz" not in flist


sample_aliases = factories.sample_layout(
    samples=['CHS.HG00512', 'CHS.HG00513', 'CHS.HG00512'],
    sample_aliases=['s1', 's1', 's2'],
    platform_units=['010101_AAABBB11XX', '020202_AAABBB22XX', '010101_AAABBB11XX'],
    paired_end=[True] * 3,
    dirname="samplealiases",
    runfmt="{SM}/{SM}_{PU}",
    numbered=True,
    scope="function",
)


def test_sample_aliases(sample_aliases):
    d = {str(x.basename): str(x.realpath().basename) for x in sample_aliases.visit() if str(x).endswith("fastq.gz")}
    assert sample_aliases.basename == "samplealiases0"
    assert d["s1_010101_AAABBB11XX_1.fastq.gz"] == "CHS.HG00512_1.fastq.gz"
    assert d["s1_020202_AAABBB22XX_1.fastq.gz"] == "CHS.HG00513_1.fastq.gz"
    assert d["s2_010101_AAABBB11XX_1.fastq.gz"] == "CHS.HG00512_1.fastq.gz"


def test_fileset_fixture_raises():
    with pytest.raises(AssertionError):
        factories.fileset(src="foo")
    with pytest.raises(AssertionError):
        factories.fileset(src=["foo"], dst="bar")


bamset = factories.fileset(src=PURFILES, fdir="bamset", scope="function")


def test_fileset_fixture(bamset):
    flist = sorted([x.basename for x in bamset.visit() if x.basename != ".lock"])
    assert flist == sorted([os.path.basename(x) for x in PURFILES])

dstfiles = ["foo.fastq.gz", "bar.fastq.gz"]
bamset2 = factories.fileset(src=PURFILES, dst=dstfiles, fdir="bamset2", scope="function")


def test_fileset_fixture_dst(bamset2):
    flist = sorted([x.basename for x in bamset2.visit() if x.basename != ".lock"])
    assert flist == sorted(dstfiles)
    flist = sorted([x.realpath() for x in bamset2.visit() if x.basename != ".lock"])
    assert flist[0] == bamfile_realpath


##############################
# Applications
##############################
# Application test config
fixtures = application_fixtures()


@pytest.fixture(scope="function", autouse=False, params=fixtures,
                ids=["{} {}:{}/{}".format(x[0], x[1], x[2], x[3]) for x in fixtures])
def ao(request, tmpdir_factory):
    app, command, version, end, fmtdict = request.param
    params = {'version': version, 'end': end}
    outputs = [fmt.format(**params) for fmt in fmtdict.values()]
    sources = [os.path.join("applications", app, output) for output in outputs]
    dests = [os.path.basename(src) for src in sources]
    fdir = os.path.join(app, str(version), command, end)
    pdir = safe_mktemp(tmpdir_factory, fdir)
    for src, dst in zip(sources, dests):
        p = safe_symlink(pdir, src, dst)
    return pdir


def test_application_output(ao):
    for p in ao.visit():
        assert p.exists()


def test_application_fixture_params():
    c = application_fixtures(application="samtools")
    assert isinstance(c, list)


def test_call_application_output():
    with pytest.raises(AssertionError):
        factories.application_output("foo", "bar", "0.0")
    factories.application_output("samtools", "samtools_flagstat", "1.2")


appout = factories.application_output("samtools", "samtools_flagstat", "1.2")


def test_factory_application_output(appout):
    assert appout.exists()

appout_dir = factories.application_output("samtools", "samtools_flagstat", "1.2", fdir="samtools/samtools_flagstat")


def test_factory_application_output_fdir(appout_dir):
    assert appout_dir.exists()
    assert "samtools/samtools_flagstat" in str(appout_dir)


def test_init():
    from pytest_ngsfixtures import ROOT_DIR, ROOTDIR
    print(ROOT_DIR)
    print(ROOTDIR)

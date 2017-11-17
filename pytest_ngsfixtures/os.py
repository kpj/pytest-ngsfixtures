# -*- coding: utf-8 -*-
import os
import py


def safe_copy(p, src, dst):
    """Safely copy fixture file.

    Copy file from src to dst in LocalPath p. If src, dst are strings,
    they will be joined to p, assuming they are relative to p. If src,
    dst are LocalPath instances, they are left alone since LocalPath
    objects are always absolute paths.

    Args:
      p (LocalPath): path in which link is setup
      src (str, LocalPath): source file that link points to. If string, assume relative to pytest_ngsfixtures data directory
      dst (str, LocalPath): link destination name. If string, assume relative to path and concatenate; else leave alone

    Returns:
      dst (LocalPath): link name
    """
    if isinstance(src, str):
        if not os.path.isabs(src):
            src = os.path.join(DATADIR, src)
        src = py.path.local(src)
    if dst is None:
        dst = src.basename
    if isinstance(dst, str):
        dst = p.join(dst)
    if not dst.check(link=1):
        dst.dirpath().ensure(dir=True)
        src.copy(dst)
    else:
        logger.warn("link {dst} -> {src} already exists! skipping...".format(src=src, dst=dst))
    return dst


def safe_symlink(p, src, dst):
    """Safely make symlink.

    Make symlink from src to dst in LocalPath p. If src, dst are
    strings, they will be joined to p, assuming they are relative to
    p. If src, dst are LocalPath instances, they are left alone since
    LocalPath objects are always absolute paths.

    Args:
      p (LocalPath): path in which link is setup
      src (str, LocalPath): source file that link points to. If string, assume relative to pytest_ngsfixtures data directory
      dst (str, LocalPath): link destination name. If string, assume relative to path and concatenate; else leave alone

    Returns:
      dst (LocalPath): link name
    """
    if isinstance(src, str):
        if not os.path.isabs(src):
            src = os.path.join(DATADIR, src)
        src = py.path.local(src)
    if dst is None:
        dst = src.basename
    if isinstance(dst, str):
        dst = p.join(dst)
    if not dst.check(link=1):
        dst.dirpath().ensure(dir=True)
        dst.mksymlinkto(src)
    else:
        logger.warn("link {dst} -> {src} already exists! skipping...".format(src=src, dst=dst))
    return dst


def safe_mktemp(tmpdir_factory, dirname=None, **kwargs):
    """Safely make directory"""
    if dirname is None:
        return tmpdir_factory.getbasetemp()
    else:
        p = tmpdir_factory.getbasetemp().join(os.path.dirname(dirname)).ensure(dir=True)
        if kwargs.get("numbered", False):
            p = tmpdir_factory.mktemp(dirname)
        else:
            p = tmpdir_factory.getbasetemp().join(dirname)
            if not p.check(dir=1):
                p = tmpdir_factory.mktemp(dirname, numbered=False)
        return p


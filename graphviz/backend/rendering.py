r"""Render DOT source files with Graphviz ``dot``.

>>> doctest_mark_exe()

>>> import pathlib
>>> import warnings
>>> import graphviz

>>> graphviz.render('dot')
Traceback (most recent call last):
    ...
graphviz.exceptions.RequiredArgumentError: format: (required if outfile is not given, got None)

>>> graphviz.render('dot', 'svg')
Traceback (most recent call last):
    ...
graphviz.exceptions.RequiredArgumentError: filepath: (required if outfile is not given, got None)

>>> graphviz.render('dot', outfile='spam.mp3')  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
Traceback (most recent call last):
    ...
graphviz.exceptions.RequiredArgumentError:
cannot infer rendering format from suffix '.mp3' of outfile: 'spam.mp3'
(provide format or outfile with a suffix from ['.bmp', ...])

>>> source = pathlib.Path('doctest-output/spam.gv')
>>> source.write_text('graph { spam }', encoding='ascii')
14

>>> graphviz.render('dot', 'png', source) # doctest: +ELLIPSIS
'doctest-output...spam.gv.png'

>>> outfile_png =source.with_suffix('.png')
>>> graphviz.render('dot', 'png', source, outfile=outfile_png)  # doctest: +ELLIPSIS
'doctest-output...spam.png'

>>> outfile_dot = source.with_suffix('.dot')
>>> with warnings.catch_warnings(record=True) as captured:
...     graphviz.render('dot', 'plain', source, outfile=outfile_dot)  # doctest: +ELLIPSIS
'doctest-output...spam.dot'
>>> print(*[repr(w.message) for w in captured])  # doctest: +NORMALIZE_WHITESPACE
UserWarning("expected format 'dot' from outfile differs from given format: 'plain'")

>>> graphviz.render('dot', 'gv', source, outfile=str(source))
Traceback (most recent call last):
    ...
ValueError: outfile 'spam.gv' must be different from input file 'spam.gv'

>>> graphviz.render('dot', outfile=source.with_suffix('.pdf'))  # doctest: +ELLIPSIS
'doctest-output...spam.pdf'

>>> import os
>>> render = source.parent / 'render'
>>> os.makedirs(render, exist_ok=True)
>>> outfile_render = render / source.with_suffix('.pdf').name
>>> graphviz.render('dot', filepath=source, outfile=outfile_render)  # doctest: +ELLIPSIS
'doctest-output...render...spam.pdf'

>>> graphviz.render('dot', outfile='spam.png', raise_if_exists=True, overwrite=True)
Traceback (most recent call last):
    ...
ValueError: overwrite cannot be combined with raise_if_exists

>>> graphviz.render('dot', outfile=outfile_png, raise_if_exists=True)  # doctest: +ELLIPSIS
Traceback (most recent call last):
FileExistsError: output file exists: 'doctest-output...spam.png'

>>> graphviz.render('dot', 'jpg', outfile='doctest-output/spam.jpeg')  # doctest: +ELLIPSIS
'doctest-output...spam.jpeg'

>>> with warnings.catch_warnings(record=True) as captured:
...     graphviz.render('dot', 'png', outfile='doctest-output/spam.peng')  # doctest: +ELLIPSIS
'doctest-output...spam.peng'
>>> print(*[repr(w.message) for w in captured])  # doctest: +NORMALIZE_WHITESPACE
UserWarning("unknown outfile suffix '.peng' (expected: '.png')")
"""

import os
import typing
import warnings

from .._defaults import DEFAULT_SOURCE_EXTENSION
from .. import _tools
from .. import exceptions
from .. import parameters

from . import dot_command
from . import execute

__all__ = ['render']


def get_supported_formats() -> typing.List[str]:
    """Return a sorted list of supported formats for exception/warning messages.

    >>> get_supported_formats()  # doctest: +ELLIPSIS
    ['bmp', ...]
    """
    return sorted(parameters.FORMATS)


def get_supported_suffixes() -> typing.List[str]:
    """Return a sorted list of supported outfile suffixes for exception/warning messages.

    >>> get_supported_suffixes()  # doctest: +ELLIPSIS
    ['.bmp', ...]
    """
    return [f'.{format}' for format in get_supported_formats()]


@typing.overload
def render(engine: str,
           format: str,
           filepath: typing.Union[os.PathLike, str],
           renderer: typing.Optional[str] = ...,
           formatter: typing.Optional[str] = ...,
           quiet: bool = ..., *,
           outfile: typing.Optional[str] = ...,
           raise_if_exists: bool = ...,
           overwrite: bool = ...) -> str:
    """Require ``format`` and ``filepath`` with default ``outfile=None``."""


@typing.overload
def render(engine: str,
           format: typing.Optional[str] = ...,
           filepath: typing.Optional[typing.Union[os.PathLike, str]] = ...,
           renderer: typing.Optional[str] = ...,
           formatter: typing.Optional[str] = ...,
           quiet: bool = False, *,
           outfile: typing.Optional[str] = ...,
           raise_if_exists: bool = ...,
           overwrite: bool = ...) -> str:
    """Optional ``format`` and ``filepath`` with given ``outfile``."""


@typing.overload
def render(engine: str,
           format: typing.Optional[str] = ...,
           filepath: typing.Optional[typing.Union[os.PathLike, str]] = ...,
           renderer: typing.Optional[str] = ...,
           formatter: typing.Optional[str] = ...,
           quiet: bool = False, *,
           outfile: typing.Optional[str] = ...,
           raise_if_exists: bool = ...,
           overwrite: bool = ...) -> str:
    """Required/optional ``format`` and ``filepath`` depending on ``outfile``."""


@_tools.deprecate_positional_args(supported_number=3)
def render(engine: str,
           format: typing.Optional[str] = None,
           filepath: typing.Optional[typing.Union[os.PathLike, str]] = None,
           renderer: typing.Optional[str] = None,
           formatter: typing.Optional[str] = None,
           quiet: bool = False, *,
           outfile: typing.Optional[str] = None,
           raise_if_exists: bool = False,
           overwrite: bool = False) -> str:
    """Render file with ``engine`` into ``format`` and return result filename.

    Args:
        engine: Layout engine for rendering (``'dot'``, ``'neato'``, ...).
        format: Output format for rendering (``'pdf'``, ``'png'``, ...).
        filepath: Path to the DOT source file to render.
        renderer: Output renderer (``'cairo'``, ``'gd'``, ...).
        formatter: Output formatter (``'cairo'``, ``'gd'``, ...).
        quiet: Suppress ``stderr`` output from the layout subprocess.
        outfile: Path for the rendered output file.
        raise_if_exits: Raise :exc:`FileExistError` if the result file exists.
        overwrite: Allow ``dot`` to write to the file it reads from.
            Incompatible with raise_if_exists.

    Returns:
        The (possibly relative) path of the rendered file.

    Raises:
        ValueError: If ``engine``, ``format``, ``renderer``, or ``formatter``
            are unknown.
        graphviz.RequiredArgumentError: If ``format`` or ``filepath`` are None
            unless ``outfile`` is given.
        graphviz.RequiredArgumentError: If ``formatter`` is given
            but ``renderer`` is None.
        ValueError: If ``outfile`` and ``filename`` are the same file
            unless ``overwite=True``.
        graphviz.ExecutableNotFound: If the Graphviz 'dot' executable
            is not found.
        graphviz.CalledProcessError: If the returncode (exit status)
            of the rendering 'dot' subprocess is non-zero.
        FileExitsError: If ``raise_if_exists`` and the result file exists.

    Note:
        The layout command is started from the directory of ``filepath``,
        so that references to external files
        (e.g. ``[image=images/camelot.png]``)
        can be given as paths relative to the DOT source file.
    """
    if raise_if_exists and overwrite:
        raise ValueError('overwrite cannot be combined with raise_if_exists')

    if outfile is not None:
        # https://www.graphviz.org/doc/info/command.html#-o
        format = get_rendering_format(outfile, format=format)

        cmd = dot_command.command(engine, format,
                                  renderer=renderer, formatter=formatter)

        if filepath is None:
            outfile_stem, _ = os.path.splitext(outfile)
            filepath = f'{outfile_stem}.{DEFAULT_SOURCE_EXTENSION}'

        dirname, filename = os.path.split(filepath)
        outfile_dirname, outfile_filename = os.path.split(outfile)
        del filepath

        if (outfile_filename == filename
            and os.path.abspath(outfile_dirname) == os.path.abspath(dirname)
            and not overwrite):  # noqa: E129
            raise ValueError(f'outfile {outfile_filename!r} must be different'
                             f' from input file {filename!r}')

        if outfile_dirname != dirname:
            outfile_filename = os.path.abspath(outfile)

        cmd += ['-o', outfile_filename, filename]

        rendered = os.fspath(outfile)
    elif format is None:
        raise exceptions.RequiredArgumentError('format: (required if outfile is not given,'
                                             f' got {format!r})')
    elif filepath is None:
        raise exceptions.RequiredArgumentError('filepath: (required if outfile is not given,'
                                             f' got {filepath!r})')
    else:
        # https://www.graphviz.org/doc/info/command.html#-O
        cmd = dot_command.command(engine, format,
                                  renderer=renderer, formatter=formatter)

        dirname, filename = os.path.split(filepath)
        del filepath

        cmd += ['-O', filename]

        suffix_args = (formatter, renderer, format)
        suffix = '.'.join(a for a in suffix_args if a is not None)

        rendered = os.path.join(dirname, f'{filename}.{suffix}')

    if raise_if_exists and os.path.exists(rendered):
        raise FileExistsError(f'output file exists: {rendered!r}')

    execute.run_check(cmd, cwd=dirname or None,
                      quiet=quiet, capture_output=True,)
    return rendered


def get_rendering_format(outfile: typing.Union[os.PathLike, str], *,
                         format: typing.Optional[str]) -> str:
    """Return format from outfile suffix and/or given format."""
    try:
        result = _get_rendering_format(outfile)
    except ValueError:
        _, suffix = os.path.splitext(outfile)
        if format is None:
            msg = (f'cannot infer rendering format from suffix {suffix!r}'
                   f' of outfile: {outfile!r} (provide format or outfile'
                   f' with a suffix from {get_supported_suffixes()!r})')
            raise exceptions.RequiredArgumentError(msg)

        warnings.warn(f'unknown outfile suffix {suffix!r} (expected: {"." + format!r})')
        return format
    else:
        assert result is not None
        if format is not None and format.lower() != result:
            warnings.warn(f'expected format {result!r} from outfile'
                          f' differs from given format: {format!r}')

        return result


def _get_rendering_format(outfile: typing.Union[os.PathLike, str]) -> str:
    """Return format inferred from outfile suffix.

    >>> _get_rendering_format('spam.pdf')  # doctest: +NO_EXE
    'pdf'

    >>> import pathlib
    >>> _get_rendering_format(pathlib.Path('spam.gv.svg'))
    'svg'

    >>> _get_rendering_format('spam.PNG')
    'png'

    >>> _get_rendering_format('spam')
    Traceback (most recent call last):
        ...
    ValueError: cannot infer rendering format from outfile: 'spam' (missing suffix)

    >>> _get_rendering_format('spam.mp3')  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
        ...
    ValueError: cannot infer rendering format from outfile: 'spam.mp3'
        (unknown format: 'mp3' must be one of [...])
    """
    _, suffix = os.path.splitext(outfile)
    if not suffix:
        raise ValueError('cannot infer rendering format from outfile:'
                         f' {outfile!r} (missing suffix)')

    start, sep, format_ = suffix.partition('.')
    assert sep and not start, f"{suffix}.startswith('.')"
    format_ = format_.lower()

    try:
        parameters.verify_format(format_)
    except ValueError:
        raise ValueError('cannot infer rendering format from outfile:'
                         f' {outfile!r} (unknown format: {format_!r}'
                         f' must be one of {get_supported_formats()!r})')
    return format_

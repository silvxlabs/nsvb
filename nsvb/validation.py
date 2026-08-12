"""
Input validation for the NSVB estimators.

The models are unguarded power functions, so an out-of-domain input does not
fail loudly -- it produces something that looks like an answer. A negative
diameter raises a real number to a fractional power and yields a *complex*
number; a broken-top height above total height does the same via
``(1 - AH/H)``; ``CULL > 100`` produces negative sound volumes; a DECAYCD of 6
reaches a bare ``KeyError: ('H', 6)`` from a table lookup. None of those is
distinguishable from a valid result by a caller processing a batch.

Everything here is applied through the :func:`validated` decorator, which runs
once at the outermost estimator call. NSVB functions are heavily composed --
``carbon_content`` reaches ``total_inside_bark_wood_volume`` through about ten
frames -- so a context flag suppresses re-validation on the way down. That
keeps the error message anchored to the function the caller actually invoked
and avoids paying for the checks ten times per tree.

Missing data is deliberately *not* an error. ``NaN`` propagates through every
check, so a batch containing trees with unrecorded heights yields ``NaN`` for
those rows rather than aborting the whole array. ``ah`` and ``cr`` also use
``NaN``/``None`` as their legitimate "not applicable" marker.
"""

import contextvars
import functools
import inspect

import numpy as np

from nsvb.tables import REF_SPECIES, resolve_stdorgcd

# NSVB stump height (ft). A broken top below this is not a standing tree.
STUMP_HEIGHT_FT = 1.0

# FIA decay class codes. 0 is our convention for "live"; 1-5 are the FIA
# standing-dead codes covered by GTR table 1.
VALID_DECAY_CLASSES = (0, 1, 2, 3, 4, 5)

# Parameters the decorator knows how to check, in the order errors are
# reported. Anything else in a signature is passed through untouched.
_CHECKED = ("spcd", "dia", "ht", "cull", "ah", "cr", "decaycd", "stdorgcd")

# Array-like parameters that should accept lists and tuples, as the ArrayLike
# type hints advertise.
_ARRAYLIKE = ("spcd", "dia", "ht", "division", "cull", "ah", "cr", "decaycd",
              "province", "stdorgcd")

_validating = contextvars.ContextVar("nsvb_validating", default=False)


# Plain Python numbers are by far the common case for scalar calls, and
# np.asarray on each of seven parameters costs more than the estimator itself.
# _scalar() returns a float for those and None for anything array-like, letting
# each check take a branch that touches numpy only when it has to.
_PLAIN_NUMBERS = (int, float, np.integer, np.floating)


def _scalar(value):
    """The value as a plain float if it is a scalar, else None."""
    if value is None:
        return float("nan")
    if isinstance(value, _PLAIN_NUMBERS):
        return float(value)
    return None


def _floats(value):
    """As a float array, with None meaning 'absent' (NaN)."""
    if value is None:
        return np.asarray(np.nan, dtype=float)
    return np.asarray(value, dtype=float)


def _finite(values):
    """Mask of entries that carry an actual value (not NaN/None)."""
    return np.isfinite(values)


def _isnan(x):
    return x != x


def check_spcd(spcd):
    quick = _scalar(spcd)
    if quick is not None:
        if int(quick) not in REF_SPECIES:
            raise ValueError(
                f"unknown FIA species code (SPCD): {int(quick)}. "
                f"SPCD must appear in the FIADB REF_SPECIES table."
            )
        return
    codes = np.asarray(spcd)
    unknown = sorted({int(s) for s in codes.reshape(-1)
                      if int(s) not in REF_SPECIES})
    if unknown:
        raise ValueError(
            f"unknown FIA species code (SPCD): {unknown[:10]}"
            f"{' ...' if len(unknown) > 10 else ''}. "
            f"SPCD must appear in the FIADB REF_SPECIES table."
        )


def check_dia(dia):
    quick = _scalar(dia)
    if quick is not None:
        if not _isnan(quick) and quick <= 0:
            raise ValueError(
                f"diameter at breast height (dia) must be positive; got {quick}. "
                f"Use NaN for a missing measurement."
            )
        return
    values = _floats(dia)
    bad = _finite(values) & (values <= 0)
    if np.any(bad):
        raise ValueError(
            f"diameter at breast height (dia) must be positive; got "
            f"{values[bad].reshape(-1)[:5] if values.ndim else values}. "
            f"Use NaN for a missing measurement."
        )


def check_ht(ht):
    quick = _scalar(ht)
    if quick is not None:
        if not _isnan(quick) and quick <= 0:
            raise ValueError(
                f"total height (ht) must be positive; got {quick}. "
                f"Use NaN for a missing measurement."
            )
        return
    values = _floats(ht)
    bad = _finite(values) & (values <= 0)
    if np.any(bad):
        raise ValueError(
            f"total height (ht) must be positive; got "
            f"{values[bad].reshape(-1)[:5] if values.ndim else values}. "
            f"Use NaN for a missing measurement."
        )


def check_cull(cull):
    quick = _scalar(cull)
    if quick is not None:
        if not _isnan(quick) and not 0 <= quick <= 100:
            raise ValueError(
                f"cull must be a percentage between 0 and 100; got {quick}. "
                f"Values above 100 produce negative sound volumes."
            )
        return
    values = _floats(cull)
    bad = _finite(values) & ((values < 0) | (values > 100))
    if np.any(bad):
        raise ValueError(
            f"cull must be a percentage between 0 and 100; got "
            f"{values[bad].reshape(-1)[:5] if values.ndim else values}. "
            f"Values above 100 produce negative sound volumes."
        )


def check_ah(ah, ht):
    """Broken-top actual height: between the stump and total height."""
    quick_ah, quick_ht = _scalar(ah), _scalar(ht)
    if quick_ah is not None and quick_ht is not None:
        if _isnan(quick_ah):
            return
        if not _isnan(quick_ht) and quick_ah > quick_ht:
            raise ValueError(
                "broken-top actual height (ah) cannot exceed total height (ht); "
                f"got ah={quick_ah} against ht={quick_ht}. "
                "A tree with an intact top should pass ah=None."
            )
        if quick_ah < STUMP_HEIGHT_FT:
            raise ValueError(
                f"broken-top actual height (ah) must be at least the "
                f"{STUMP_HEIGHT_FT}-ft stump height; got {quick_ah}. "
                f"Below the stump the merchantable volume basis goes negative."
            )
        return
    values, heights = _floats(ah), _floats(ht)
    present = _finite(values)
    if not np.any(present):
        return
    too_tall = present & _finite(heights) & (values > heights)
    if np.any(too_tall):
        raise ValueError(
            "broken-top actual height (ah) cannot exceed total height (ht); "
            f"got ah={values[too_tall].reshape(-1)[:5] if values.ndim else values} "
            f"against ht={heights[too_tall].reshape(-1)[:5] if heights.ndim else heights}. "
            "A tree with an intact top should pass ah=None."
        )
    too_low = present & (values < STUMP_HEIGHT_FT)
    if np.any(too_low):
        raise ValueError(
            f"broken-top actual height (ah) must be at least the {STUMP_HEIGHT_FT}-ft "
            f"stump height; got "
            f"{values[too_low].reshape(-1)[:5] if values.ndim else values}. "
            f"Below the stump the merchantable volume basis goes negative."
        )


def check_cr(cr):
    quick = _scalar(cr)
    if quick is not None:
        if not _isnan(quick) and not 0 < quick <= 1:
            raise ValueError(
                f"crown ratio (cr) is a decimal fraction in (0, 1]; got {quick}. "
                f"A crown ratio of 30 percent is cr=0.30, not cr=30."
            )
        return
    values = _floats(cr)
    bad = _finite(values) & ((values <= 0) | (values > 1))
    if np.any(bad):
        raise ValueError(
            f"crown ratio (cr) is a decimal fraction in (0, 1]; got "
            f"{values[bad].reshape(-1)[:5] if values.ndim else values}. "
            f"A crown ratio of 30 percent is cr=0.30, not cr=30."
        )


def check_decaycd(decaycd):
    quick = _scalar(decaycd)
    if quick is not None:
        if _isnan(quick):
            return
        if quick != int(quick):
            raise ValueError(
                f"decay class (decaycd) must be a whole number; got {quick}. "
                f"A fractional value would be silently truncated."
            )
        if int(quick) not in VALID_DECAY_CLASSES:
            raise ValueError(
                f"decay class (decaycd) must be one of {VALID_DECAY_CLASSES} "
                f"(0 = live, 1-5 = FIA standing-dead codes); got {int(quick)}."
            )
        return
    values = _floats(decaycd)
    present = _finite(values)
    fractional = present & (values != np.floor(values))
    if np.any(fractional):
        raise ValueError(
            f"decay class (decaycd) must be a whole number; got "
            f"{values[fractional].reshape(-1)[:5] if values.ndim else values}. "
            f"A fractional value would be silently truncated."
        )
    out_of_range = present & ~np.isin(values, VALID_DECAY_CLASSES)
    if np.any(out_of_range):
        raise ValueError(
            f"decay class (decaycd) must be one of {VALID_DECAY_CLASSES} "
            f"(0 = live, 1-5 = FIA standing-dead codes); got "
            f"{values[out_of_range].reshape(-1)[:5] if values.ndim else values}."
        )


def check_stdorgcd(stdorgcd):
    if isinstance(stdorgcd, np.ndarray):
        for value in stdorgcd.reshape(-1):
            resolve_stdorgcd(value)
    else:
        resolve_stdorgcd(stdorgcd)


_CHECKERS = {
    "spcd": check_spcd,
    "dia": check_dia,
    "ht": check_ht,
    "cull": check_cull,
    "cr": check_cr,
    "decaycd": check_decaycd,
    "stdorgcd": check_stdorgcd,
}


def validate(arguments):
    """Run every applicable check over a mapping of parameter name -> value."""
    for name in _CHECKED:
        if name not in arguments:
            continue
        value = arguments[name]
        if name == "ah":
            check_ah(value, arguments.get("ht"))
        else:
            _CHECKERS[name](value)


def _normalize(arguments):
    """Accept lists and tuples wherever ArrayLike is advertised."""
    for name in _ARRAYLIKE:
        value = arguments.get(name)
        if isinstance(value, (list, tuple)):
            arguments[name] = np.asarray(value)


def validated(fn):
    """Validate and normalize the standard tree attributes of ``fn``.

    Runs only at the outermost estimator call: NSVB functions compose deeply
    -- ``carbon_content`` reaches ``total_inside_bark_wood_volume`` through
    about ten frames -- so re-checking at every level would multiply the cost
    and report errors against an internal helper rather than the function the
    caller actually named.

    Deliberately avoids ``inspect.Signature.bind``, which dominated the cost
    when measured (it roughly doubled a scalar call). The parameter names and
    defaults are captured once at decoration time and the mapping is rebuilt
    with a plain dict update, and the original ``args``/``kwargs`` are passed
    straight through unless a list or tuple actually needed converting.
    """
    parameters = inspect.signature(fn).parameters
    names = tuple(parameters)
    defaults = {
        name: param.default
        for name, param in parameters.items()
        if param.default is not inspect.Parameter.empty
    }
    # Only these need checking; skip the bookkeeping entirely for the rest.
    relevant = tuple(n for n in names if n in _CHECKED or n in _ARRAYLIKE)

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if _validating.get():
            return fn(*args, **kwargs)
        if len(args) > len(names):
            raise TypeError(
                f"{fn.__name__}() takes at most {len(names)} positional "
                f"arguments but {len(args)} were given"
            )
        arguments = dict(defaults)
        arguments.update(zip(names, args))
        arguments.update(kwargs)

        needs_normalizing = any(
            isinstance(arguments.get(name), (list, tuple)) for name in relevant
        )
        if needs_normalizing:
            _normalize(arguments)
        validate(arguments)

        token = _validating.set(True)
        try:
            if needs_normalizing:
                return fn(**arguments)
            return fn(*args, **kwargs)
        finally:
            _validating.reset(token)

    return wrapper

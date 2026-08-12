from typing import Union

import numpy as np
from numpy.typing import ArrayLike, NDArray


def schumacher_hall_method(
    dia: Union[float, ArrayLike], ht: Union[float, ArrayLike], **kwargs
) -> Union[float, NDArray]:
    """
    Schumacher-Hall Method.

    Equation (1) in the GTR.

    Parameters:
        dia (float): Diameter of the tree.
        ht (float): Height of the tree.
        a (float): Coefficient.
        b (float): Exponent for diameter.
        c (float): Exponent for height.
        e (float, optional): Constant. Default is 0.
    """
    a = kwargs.get("a")
    b = kwargs.get("b")
    c = kwargs.get("c")
    e = kwargs.get("e", 0)
    return a * (dia**b) * (ht**c) + e


def segmented_model(
    dia: Union[float, ArrayLike], ht: Union[float, ArrayLike], **kwargs
) -> Union[float, NDArray]:
    """
    Segmented Model.

    Equation (2) in the GTR.

    Parameters:
        dia (float): Diameter of the tree.
        ht (float): Height of the tree.
        a (float): Coefficient.
        b (float): Exponent for diameter for dia < k.
        b1 (float): Exponent for diameter for dia >= k.
        c (float): Exponent for height.
        k (float): Segment threshold.
        e (float, optional): Constant. Default is 0.
    """
    a = kwargs.get("a")
    b = kwargs.get("b")
    b1 = kwargs.get("b1")
    c = kwargs.get("c")
    k = kwargs.get("k")
    e = kwargs.get("e", 0)
    return np.where(
        dia < k,
        a * (dia**b) * (ht**c) + e,
        a * (k ** (b - b1)) * (dia**b1) * (ht**c) + e,
    )


def continuously_variable_model(
    dia: Union[float, ArrayLike], ht: Union[float, ArrayLike], **kwargs
) -> Union[float, NDArray]:
    """
    Continuously Variable Model.

    Equation (3) in the GTR:

        y = a * D^[a1 * (1 - exp(-b*D))^c1] * H^c

    Note the grouping of the diameter exponent: ``c1`` raises only
    ``(1 - exp(-b*D))``; it does NOT raise ``a1 * (1 - exp(-b*D))``. GTR p.8
    prints c1 as a superscript on the closing parenthesis of
    ``(1 - exp(-b*D_i))``, with no outer parenthesis enclosing the ``a1``
    factor.

    The distinction is not cosmetic -- the wrong grouping under-predicts by
    3-7x for the four species that use this form. Three independent checks:

      * Asymptotically D -> inf drives ``(1 - exp(-b*D)) -> 1``, so the
        diameter exponent tends to ``a1``, which is 1.63-1.99 across the four
        model-3 rows -- the right neighbourhood for volume and biomass
        allometry. The wrong grouping tends to ``a1^c1``, i.e. 1.16-1.53.
      * SPCD 800 (oak spp.) total inside-bark volume lands within 8 percent of
        that species' own Jenkins-group model under this grouping, and 3-7x
        below it under the other.
      * SPCD 111 (slash pine) S8a has a model-3 row for planted stands and a
        model-2 row for natural stands. Model 2 is unaffected by the
        ambiguity, so it anchors the answer: the two origins agree closely
        under this grouping and differ by ~5x under the other.

    None of the GTR's four worked examples uses model 3, so the published
    examples cannot discriminate between the readings.

    Parameters:
        dia (float): Diameter of the tree.
        ht (float): Height of the tree.
        a (float): Coefficient.
        a1 (float): Asymptotic diameter exponent.
        b (float): Rate coefficient inside the exponential.
        c (float): Exponent for height.
        c1 (float): Exponent applied to (1 - exp(-b*D)).
        e (float, optional): Constant. Default is 0.
    """
    a = kwargs.get("a")
    a1 = kwargs.get("a1")
    b = kwargs.get("b")
    c = kwargs.get("c")
    c1 = kwargs.get("c1")
    e = kwargs.get("e", 0)
    dia_exponent = a1 * (1 - np.exp(-b * dia)) ** c1
    return a * (dia**dia_exponent) * (ht**c) + e


def modifed_wiley_model(
    dia: Union[float, ArrayLike], ht: Union[float, ArrayLike], **kwargs
) -> Union[float, NDArray]:
    """
    Modified Wiley Model.

    Equation (4) in the GTR.

    Parameters:
        dia (float): Diameter of the tree.
        ht (float): Height of the tree.
        a (float): Coefficient.
        b (float): Exponent for diameter.
        b1 (float): Exponent.
        c (float): Exponent for height.
        e (float, optional): Constant. Default is 0.
    """
    a = kwargs.get("a")
    b = kwargs.get("b")
    b1 = kwargs.get("b1")
    c = kwargs.get("c")
    e = kwargs.get("e", 0)
    return a * (dia**b) * (ht**c) * np.exp(-(b1 * dia)) + e


def modified_schumaker_hall(
    dia: Union[float, ArrayLike], ht: Union[float, ArrayLike], **kwargs
) -> Union[float, NDArray]:
    """
    Modified Schumacher-Hall Method.

    Parameters:
        dia (float): Diameter of the tree.
        ht (float): Height of the tree.
        a (float): Coefficient.
        b (float): Exponent for diameter.
        c (float): Exponent for height.
        wdsg (float): Wood specific gravity.
        e (float, optional): Constant. Default is 0.
    """
    a = kwargs.get("a")
    b = kwargs.get("b")
    c = kwargs.get("c")
    wdsg = kwargs.get("wdsg")
    e = kwargs.get("e", 0)
    return a * (dia**b) * (ht**c) * wdsg + e


MODEL_MAP = {
    1: schumacher_hall_method,
    2: segmented_model,
    3: continuously_variable_model,
    4: modifed_wiley_model,
    5: modified_schumaker_hall,
}

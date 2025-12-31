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
        a * (k ** (b - b1)) * (dia**b1) * (ht**c) + e
    )


def continuously_variable_model(
    dia: Union[float, ArrayLike], ht: Union[float, ArrayLike], **kwargs
) -> Union[float, NDArray]:
    """
    Continuously Variable Model.

    Equation (3) in the GTR-WO-104 (page 11):
    y = a × D^(a1 × (1 - exp(-b × D))^c1) × H^c

    Parameters:
        dia (float): Diameter of the tree.
        ht (float): Height of the tree.
        a (float): Coefficient.
        a1 (float): Coefficient in diameter exponent.
        b (float): Coefficient in exponential term.
        c (float): Exponent for height.
        c1 (float): Exponent for the (1 - exp) term.
        e (float, optional): Constant. Default is 0.
    """
    a = kwargs.get("a")
    a1 = kwargs.get("a1")
    b = kwargs.get("b")
    c = kwargs.get("c")
    c1 = kwargs.get("c1")
    e = kwargs.get("e", 0)
    # GTR Equation 3: y = a × D^(a1 × (1 - exp(-b × D))^c1) × H^c
    # The diameter exponent is: a1 × (1 - exp(-b × D))^c1
    diameter_exponent = a1 * ((1 - np.exp(-b * dia)) ** c1)
    return a * (dia ** diameter_exponent) * (ht ** c) + e


def modified_wiley_model(
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
    4: modified_wiley_model,
    5: modified_schumaker_hall,
}

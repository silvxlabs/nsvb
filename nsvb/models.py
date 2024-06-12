from math import exp


def schumacher_hall_method(dia: float, ht: float, **kwargs) -> float:
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


def segmented_model(dia: float, ht: float, **kwargs) -> float:
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
    if dia < k:
        return a * (dia**b) * (ht**c) + e
    return a * (k ** (b - b1)) * (dia**b1) * (ht**c) + e


def continuously_variable_model(dia: float, ht: float, **kwargs) -> float:
    """
    Continuously Variable Model.

    Equation (3) in the GTR.

    Parameters:
        dia (float): Diameter of the tree.
        ht (float): Height of the tree.
        a (float): Coefficient.
        a1 (float): Coefficient.
        b (float): Exponent for diameter.
        c (float): Exponent for height.
        c1 (float): Exponent.
        e (float, optional): Constant. Default is 0.
    """
    a = kwargs.get("a")
    a1 = kwargs.get("a1")
    b = kwargs.get("b")
    c = kwargs.get("c")
    c1 = kwargs.get("c1")
    e = kwargs.get("e", 0)
    return a * (a1 * ((1 - exp(-b * dia)) ** c1)) * (ht**c) + e


def modifed_wiley_model(dia: float, ht: float, **kwargs) -> float:
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
    return a * (dia**b) * (ht**c) * exp(-(b1 * dia)) + e


def modified_schumaker_hall(dia: float, ht: float, **kwargs) -> float:
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

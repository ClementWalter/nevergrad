from typing import Union, Tuple, Any, List
import numpy as np
# importing ParametersDict to populate parameters (fake renaming for mypy explicit reimport)
# pylint: disable=unused-import,useless-import-alias
from .core3 import Parameter
from .core3 import ParametersDict as ParametersDict  # noqa


class Array(Parameter):
    """Array variable of a given shape, on which several transforms can be applied.

    Parameters
    ----------
    sigma: float or Array
        standard deviation of a mutation
    distribution: str
        distribution of the data ("linear" or "log")
    """

    def __init__(
            self,
            shape: Tuple[int, ...],
            sigma: Union[float, "Array"] = 1.0,
            distribution: Union[str, Parameter] = "linear",
            recombination: Union[str, Parameter] = "average"
    ) -> None:
        assert not isinstance(shape, Parameter)
        super().__init__(shape=shape, sigma=sigma, distribution=distribution, recombination=recombination)
        self._value: np.ndarray = np.zeros(shape)

    @property
    def value(self) -> np.ndarray:
        return self._value

    @value.setter
    def value(self, value: np.ndarray) -> None:
        if not isinstance(value, np.ndarray):
            raise TypeError(f"Received a {type(value)} in place of a np.ndarray")
        if self._value.shape != value.shape:
            raise ValueError(f"Cannot set array of shape {self._value.shape} with value of shape {value.shape}")
        self._value = value

    # pylint: disable=unused-argument
    def with_std_data(self, data: np.ndarray, deterministic: bool = True) -> None:
        sigma = self._get_parameter_value("sigma")
        self._value = (sigma * data).reshape(self.value.shape)

    def spawn_child(self) -> "Array":
        child = super().spawn_child()
        child._value = self.value
        return child

    def to_std_data(self) -> np.ndarray:
        sigma = self._get_parameter_value("sigma")
        reduced = self._value / sigma
        return reduced.ravel()  # type: ignore

    def recombine(self, *others: "Array") -> None:
        recomb = self._get_parameter_value("recombination")
        all_p = [self] + list(others)
        if recomb == "average":
            self.with_std_data(np.mean([p.to_std_data() for p in all_p], axis=0))
        else:
            raise ValueError(f'Unknown recombination "{recomb}"')


class ParametersList(ParametersDict):
    """Handle for facilitating dict of parameters management
    """

    def __init__(self, *parameters: Any) -> None:
        super().__init__(**{str(k): p for k, p in enumerate(parameters)})

    @property  # type: ignore
    def value(self) -> List[Any]:  # type: ignore
        param_val = [x[1] for x in sorted(self._parameters.items(), key=lambda x: int(x[0]))]
        return [p.value if isinstance(p, Parameter) else p for p in param_val]

    @value.setter
    def value(self, value: List[Any]) -> None:
        assert isinstance(value, list)
        for k, val in enumerate(value):
            key = str(k)
            param = self._parameters[key]
            if not isinstance(param, Parameter):
                self._parameters[key] = val
            else:
                param.value = val
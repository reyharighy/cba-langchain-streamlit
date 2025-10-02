"""A module to manage all custom decorators for covenience usage of Streamlit decorators."""

# standard
from functools import wraps
from time import sleep
from typing import (
    Callable,
    Literal,
    ParamSpec,
    TypeVar,
)

# third-party
import streamlit as st

P = ParamSpec("P")
R = TypeVar("R")

def streamlit_status_container(
    running_text: str,
    complete_text: str,
    mockup: bool = False,
    expanded: bool = False
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Apply status container as decorator to display the process of long-running tasks.

    The status container is a dedicated element from Streamlit.
    
    Args:
        running_text: Text to display when the task is running.
        complete_text: Text to display when the task is done running.
        mockup: Set to True to simulate the running process in mockup mode.
        expanded: Set to True to make the container expendable.
    
    Results:
        The wrapped function.    
    
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with st.status(running_text, expanded=expanded) as status:
                result = func(*args, **kwargs)

                if mockup:
                    sleep(5)

                status.update(
                    label=complete_text,
                    state="complete"
                )

            return result

        return wrapper

    return decorator

def streamlit_cache(
    spinner_text: str,
    cache_type: Literal["data", "resource"]
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Wrap the default Streamlit st.cache_data decorator.

    The reason of creating this decorator is to make visible of function's docstring.
    Streamlit st.cache_data and st.cache_resource do not use wraps from functools.

    Args:
        spinner_text: Text to show when caching the result of wrapped function's computation.
        cache_type: Specify the type of function to cache.

    Returns:
        The wrapped function.

    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        if cache_type == "data":
            cached_func = st.cache_data(show_spinner=spinner_text)(func)
        else:
            cached_func = st.cache_resource(show_spinner=spinner_text)(func)

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs):
            return cached_func(*args, **kwargs)

        return wrapper

    return decorator

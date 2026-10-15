"""Freeze the calculation inputs before starting the worker thread."""
from dataclasses import dataclass
from types import SimpleNamespace


@dataclass(frozen=True)
class Value:
    value: object
    def get(self):
        return self.value


def snapshot_inputs(app):
    snapshot=SimpleNamespace(df_clean=app.df_clean.copy(deep=True),df_env=app.df_env.copy(deep=True))
    for name,value in vars(app).items():
        if name.startswith('var_') and hasattr(value,'get'):
            setattr(snapshot,name,Value(value.get()))
    return snapshot

#!/usr/bin/env python3

from pathlib import Path

import click
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import re
import seaborn as sns

import r2py.modelr as modelr


def inv_logit(p):
    """Returns the inverse logit function of the input."""
    return np.exp(p) / (1 + np.exp(p))


def read_terms_csv(model):
    fname = Path(model)
    fname = fname.parent / (fname.stem + "_variables.csv")
    return pd.read_csv(fname)


def get_min_max(terms, name):
    row = terms[terms.variableName == name]
    return (row["min"].values[0], row["max"].values[0])


@click.command()
@click.argument("model", type=click.Path(dir_okay=False))
@click.option("--title", type=str, default="Model response vs HPD", help="Plot title")
@click.option(
    "--adjust",
    type=float,
    default=0.01,
    help="Adjustment value for inverse logit transformation",
)
@click.option(
    "--save", "-s", type=click.Path(dir_okay=False), help="A file to save the plot to."
)
@click.option("--prefix", "-p", type=str)
@click.option("--clip/--no-clip", is_flag=True, default=True)
@click.option("--cs-clip/--no-cs-clip", is_flag=True, default=False)
def plot(model, title, save, adjust, prefix, clip, cs_clip):
    """Plot response curve of CS model versus HPD."""
    mod = modelr.load(model)

    #import pdb; pdb.set_trace()
    columns = tuple(filter(lambda x: re.match(prefix, x), mod.inputs))
    df = pd.DataFrame(columns=columns)
    nsteps = 30
    intercept = mod.intercept

    terms = read_terms_csv(model)
    s2_min_max = get_min_max(terms, "HPD at site 2")
    diff_min_max = get_min_max(terms, "HPD difference")

    for col in df.columns:
        s = pd.Series(
            mod.partial(
                {
                    "scale_log_hpd_s2": np.linspace(*s2_min_max, nsteps),
                    #"scale_log_hpd_diff": np.linspace(*diff_min_max, nsteps),
                    "scale_log_hpd_diff":  np.full((nsteps), 0),
                    col: np.full((nsteps), 1),
                }
            )
        )
        if clip:
            s = s.clip(*mod.output_range)
        if mod.output == "sqrtRescaledAbundance":
            vname = "Abundance"
            df[col] = np.power(s, 2) / np.power(intercept, 2)
        else:
            vname = "CompSim"
            s2 = (inv_logit(s) - adjust) / (inv_logit(intercept) - adjust)
            if cs_clip:
                s2 = s2.clip(0, 1)
            df[col] = s2
    df.index = np.linspace(*s2_min_max, nsteps)
    df = df.rename(columns=lambda c: c.replace(prefix, ""))

    df.plot()
    ax = plt.gca()
    ax.set_title(title)
    ax.set_xlabel("log(HPD + 1)")
    ax.set_ylabel(vname)

    if save:
        plt.savefig(save, transparent=False, bbox_inches="tight", pad_inches=0)
    plt.show()
    return


if __name__ == "__main__":
    matplotlib.style.use("ggplot")
    sns.set_style("darkgrid")
    plot()

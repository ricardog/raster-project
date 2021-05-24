#!/usr/bin/env python3

import click
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import re
import seaborn as sns

import projections.r2py.modelr as modelr


def inv_logit(p):
    """Returns the inverse logit function of the input."""
    return np.exp(p) / (1 + np.exp(p))


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
@click.option("--tropical", "-t", is_flag=True, default=False)
@click.option("--clip/--no-clip", is_flag=True, default=True)
@click.option("--cs-clip/--no-cs-clip", is_flag=True, default=False)
def plot(model, title, save, adjust, prefix, tropical, clip, cs_clip):
    """Plot response curve of CS model versus HPD."""
    # This is a color brewer palette
    cb = ["#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00", "#ffff33"]
    palette = sns.color_palette(cb)

    mod = modelr.load(model)

    columns = tuple(filter(lambda x: re.match(prefix, x), mod.syms))
    df = pd.DataFrame(columns=columns)
    pname1 = "forested_tropic_temperate_tropical_forest"
    pname2 = "tropic_temperate_tropical_forest_tropical_forest"

    tropical = 1 if tropical else 0
    intercept = mod.intercept

    for col in df.columns:
        s = pd.Series(
            mod.partial(
                {
                    "loghpd": np.linspace(0, 11, 13),
                    "s2_loghpd": np.linspace(0, 11, 13),
                    "hpd_diff": np.linspace(0, -11, 13),
                    pname1: tropical,
                    pname2: tropical,
                    col: np.full((13), 1),
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
    # pdb.set_trace()
    df.index = np.linspace(0, 11, 13)
    df = df.rename(columns=lambda c: c.replace(prefix, ""))

    if prefix[-3:] == "age":
        df = df.rename(columns=lambda c: "age_" + c)
        df2 = (
            pd.wide_to_long(
                df.assign(loghpd=df.index), ["age"], i="loghpd", j="Age", sep="_"
            )
            .reset_index()
            .rename(columns=lambda x: x if x != "age" else vname)
        )
        df2.Age = df2.Age.astype("category")
        sns.lineplot(
            "loghpd", vname, hue="Age", data=df2, linewidth=1.5, palette=palette
        )
    else:
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

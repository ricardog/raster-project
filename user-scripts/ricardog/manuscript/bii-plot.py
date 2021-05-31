#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt

from bokeh.io import output_file, show, save
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.palettes import Category20
from bokeh.plotting import figure


def get_data():
    hist = pd.read_csv("historical-BIIAb-npp-global-0900-2014.csv")
    hist = hist.drop("ID", axis=1)
    hist2 = pd.read_csv("historical-BIIAb-npp-reg-0900-2014.csv")
    hist = hist.append(hist2)
    hist = hist.drop("Cells", axis=1).T
    hist.columns = hist.loc["Name"].values
    hist.drop("Name", inplace=True)
    hist.index = hist.index.astype(int)

    ssp1 = pd.read_csv("ssp1_rcp2.6_image-BIIAb-npp-global-2015-2100.csv")
    ssp12 = pd.read_csv("ssp1_rcp2.6_image-BIIAb-npp-reg-2015-2100.csv")
    ssp1 = ssp1.append(ssp12)
    ssp1 = ssp1.drop(["ID", "Cells"], axis=1).T
    ssp1.columns = ssp1.loc["Name"].values
    ssp1.drop("Name", inplace=True)
    ssp1.index = ssp1.index.astype(int)

    return hist.append(ssp1).dropna()


def do_mpl(data):
    plt.plot(data.index.values.astype(int), data)
    plt.axvline(x=2015, color="Black", linewidth=2)
    plt.ylabel("BII")
    plt.xlabel("Year")
    plt.legend(data.columns)
    plt.savefig("BIIAb-hist-ssp1.png", transparent=False)
    plt.show()


def pline(p, df, col, color="black", line_width=3):
    src = ColumnDataSource(
        data={"year": df.index, "data": df[col], "name": [col for n in range(len(df))]}
    )
    p.line("year", "data", source=src, line_width=line_width, legend=col, color=color)


def do_bokeh(data):
    p = figure(title="BII")
    mypalette = Category20[min(6, 20)]
    for idx, col in enumerate(data.columns):
        if col == "Global":
            pline(p, data, "Global", "black", 4)
        else:
            pline(p, data, col, mypalette[idx], 3)
    p.add_tools(
        HoverTool(tooltips=[("Year", "@year"), ("BII", "@data"), ("Region", "@name")])
    )
    p.legend.location = "bottom_left"
    output_file("BIIAb-hist-ssp1.html")
    save(p)
    show(p)


if __name__ == "__main__":
    data = get_data()
    do_mpl(data)
    do_bokeh(data)

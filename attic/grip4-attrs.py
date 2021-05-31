#!/usr/bin/env python3

import re
import pandas as pd
from sqlalchemy import create_engine


def camel_case_split(identifier):
    matches = re.finditer(
        ".+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)", identifier
    )
    return [m.group(0) for m in matches]


def main():
    tables = {}
    fname = ("/Users/ricardog/Downloads/GRIP4_GlobalRoads/"
             "GRIP4_AttributeDescription.xlsx"
             )
    xls = pd.read_excel(fname)
    attrs = xls.loc[:, "Attribute name":"Unnamed: 8"]
    indexes = attrs[pd.isna(attrs["Attribute name"]) is False].index.tolist()
    for idx in range(0, len(indexes) - 1):
        tbl = attrs.iloc[indexes[idx] : indexes[idx + 1], :]
        name = tbl.iloc[0, 0]
        if name == "RoadSourceId":
            name = "road_source"
            tbl.columns = tbl.iloc[0, :]
            tbl = tbl.drop(tbl.index.values[0], axis=0).rename(
                columns={
                    "Source name": "source",
                    "URL (accessed from 2009-2017)": "url",
                    "Category": "category",
                }
            )
            tbl.columns.name = None
        elif name == "RoadCountry":
            continue
        else:
            words = camel_case_split(name)
            name = "_".join(words).lower()
            tbl = tbl.rename(columns={"Values": "ID", "Description": "description"})
        tbl = (
            tbl.iloc[:, 3:]
            .dropna(axis=1, how="all")
            .dropna(axis=0, how="all")
            .sort_values("ID")
        )
        tbl.index = tbl["ID"]
        tbl.index.name = None
        tbl = tbl.drop("ID", axis=1)
        tables[name] = tbl

    engine = create_engine("postgresql://postgis:postgis@192.168.0.46:5432/grip4")
    for name in tables:
        print(name)
        tbl = tables[name]
        print(tbl)
        tbl.to_sql(name, engine, if_exists="replace", index=True, index_label="id")


if __name__ == "__main__":
    main()

from setuptools import setup, find_packages

setup(
    name="projections",
    version="0.2.0",
    author="Ricardo E. Gonzalez",
    author_email="ricardog@itinerisinc.com",
    description="Spatio-temporal projections of PREDICTS models",
    python_requires=">=3.7",
    url="https://github.com/NaturalHistoryMuseum/raster-project",
    project_urls={
        "Bug Tracker": "https://github.com/NaturalHistoryMuseum/raster-project/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    install_requires=[
        "cartopy",
        "Click",
        "fiona",
        "geopandas"
        "geopy",
        "joblib",
        "matplotlib",
        "netCDF4",
        "numpy",
        "pandas",
        "projutils @ git+https://github.com/ricardog/projutils.git",
        "pylru",
        "r2py @ git+https://github.com/ricardog/r2py.git",
        "rasterset @ git+https://github.com/ricardog/rasterset.git",
        "rasterio",
        "setuptools",
        "shapely",
    ],
    extras_require={"dev": ["black", "flake8", "pylint", "pytest"]},
)

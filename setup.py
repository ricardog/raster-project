from setuptools import setup, find_packages

setup(
    name='projections',
    author="Ricardo E. Gonzalez",
    author_email="ricardog@ricardog.com",
    description="Spatio-temporal projections of R models using python",
    version='0.1',
    python_requires='>=3.6.3',
    url="https://github.com/NaturalHistoryMuseum/raster-project",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'asciitree',
        'gdal',
        'fiona',
        'geopy',
        'joblib',
        'matplotlib',
        'netCDF4',
        'numpy',
        'pandas',
        'pylru',
        'rasterio',
        'r2py @ git+https://github.com/ricardog/r2py',
        'setuptools',
        'shapely',
        'tqdm',
        'xlrd',
    ],
    entry_points='''
        [console_scripts]
        extract_values=projections.scripts.extract_values:main
        gen_hyde=projections.scripts.gen_hyde:main
        gen_sps=projections.scripts.gen_sps:main
        hyde2nc=projections.scripts.hyde2nc:main
        nc_dump=projections.scripts.nc_dump:main

        nctomp4=projections.scripts.nctomp4:main
        project=projections.scripts.project:cli
        rview=projections.scripts.rview:main
        tifftomp4=projections.scripts.tifftomp4:main
        tiffcmp=projections.scripts.tiffcmp:main
    ''',
    build_ext='''
        include_dirs=/usr/local/include
    '''
)

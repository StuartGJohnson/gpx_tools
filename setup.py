from setuptools import setup

setup(
    name='gpx-tools',
    version='0.1',
    install_requires=['gpxpy',
                      'dtw-python',
                      'numpy',
                      'scikit-image',
                      'matplotlib',
                      'matplotlib-inline',
                      'scipy',
                      'Pillow',
                      'imageio',
                      'folium'],
    packages=[],
    py_modules=[],
    scripts=['patch_gpx_spatial',
             'patch_gpx_spatial.py',
             'patch_gpx_time',
             'patch_gpx_time.py'],
    url='https://github.com/StuartGJohnson/gpx_tools',
    license='',
    author='Stuart Johnson',
    author_email='stuart.g.johnson@gmail.com',
    description='python code for patching one gpx with another via DTW'
)

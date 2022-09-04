from setuptools import setup, find_packages

setup(
    name='gpx-tools',
    version='0.1',
    install_requires=['gpxpy ==1.5.0',
                      'dtw-python ==1.2.2',
                      'numpy ==1.23.1',
                      'scikit-image ==0.19.3',
                      'matplotlib ==3.5.2',
                      'matplotlib-inline ==0.1.3',
                      'scipy ==1.9.0',
                      'Pillow ==9.2.0',
                      'imageio ==2.21.0',
                      'folium ==0.12.1.post1'],
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

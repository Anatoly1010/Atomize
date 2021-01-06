from setuptools import setup, find_packages

args = dict(
    name="liveplot",
    version="0.1.2",
    packages=find_packages(),
    install_requires=["pyqtgraph>=0.9", "pyzmq>=14.0"],
    author="Philip Reinhold",
    author_email="pcreinhold@gmail.com",
    description="System for minimal hassle, on-the-fly, dataset visualization",
    license="MIT",
    keywords="plot plotting graph graphing",
)

try:
    import py2exe, os, zmq
    os.environ["PATH"] += os.pathsep + os.path.split(zmq.__file__)[0]
    args.update(dict(
        windows=[{
            "script":"__main__.py",
            "icon_resources": [(1, "icon.ico")],
            "dest_base":"liveplot",
            }],
        data_files=[
            ('imageformats', [
                r'C:\Python27\Lib\site-packages\PyQt4\plugins\imageformats\qico4.dll'
            ]),
            ('', ['C:\Phil\code\liveplot\icon.ico'])],
        options={
            "py2exe": {
                "includes":[
                    "scipy.sparse.csgraph._validation",
                    "scipy.special._ufuncs_cxx",
                    ],
                "dll_excludes":["MSVCP90.dll"]
                }
            }
        ))

except ImportError:
    print ('py2exe not found. py2exe command not available')

setup(**args)

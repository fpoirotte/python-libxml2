import lzma
import os
import shutil
import sys
import sysconfig
import tarfile
import tempfile
import tomllib

from pathlib import Path
from setuptools import setup
from setuptools.command.bdist_wheel import bdist_wheel
from subprocess import check_call, check_output
from urllib.request import urlretrieve


# If this environment variable is set to a non-empty value,
# the temporary folder will not be deleted automatically,
# making it easier to debug compilation issues.
delete = not os.environ.get('PYTHON_LIBXML2_DO_NOT_DELETE')

# For offline installations, set LIBXML2_MIRROR to a locally-hosted mirror.
# "/<major>.<minor>/libxml2-<version>.tar.xz will automatically be appended
# to this value to form the complete URL.
mirror = os.environ.get('LIBXML2_MIRROR', "https://download.gnome.org/sources/libxml2/").rstrip('/')

# This environment variable can be used to override the path to the "make"
# command used to build libxml2 < 2.13.0.
MAKE = os.environ.get('MAKE', 'make')

# This environment variable can be used to override the path to the "autoreconf"
# command used to build libxml2 < 2.13.0.
AUTORECONF = os.environ.get('AUTORECONF', 'autoreconf')

# This environment variable can be used to override the path to the "meson"
# command used to build libxml2 >= 2.13.0.
MESON = os.environ.get('MESON', 'meson')


# Read the version from pyproject.toml
with (Path(__file__).parent / 'pyproject.toml').open('rb') as fp:
    toml = tomllib.load(fp)
version = toml['project']['version']
major, minor, patch = version.split('.', 2)
major = int(major)
minor = int(minor)

# Keep track of the current working directory for later reference
old_pwd = os.getcwd()



def build_using_autotools(libxml2, tmpdir):
    os.chdir(os.path.join(tmpdir.name, "src"))
    options = ["--%s-%s" % ("with" if v else "without", k[5:]) for (k, v) in libxml2['config'].items() if k.startswith('with_')]
    options += [
        "--with-python",
    ]

    env = dict(os.environ.items())
    env["LDFLAGS"] = "-Wl,--no-as-needed"
    check_call([AUTORECONF, "-f", "-i"])
    check_call(["./configure", *options], env=env)
    check_call([MAKE], env=env)
    check_call([MAKE, "install", f"DESTDIR={tmpdir.name}/install/"], env=env)


def build_using_meson(libxml2, tmpdir):
    options = [f"-D{k}={str(v).lower()}" for (k, v) in libxml2['config'].items() if k.startswith('with_')]
    optiosn += [
        "-Dpython=true",
    ]

    check_call([MESON, 'setup', *options, os.path.join(tmpdir.name, "build"), os.path.join(tmpdir.name, "src")])
    os.chdir(os.path.join(tmpdir.name, "build"))
    env = dict(os.environ.items())
    env["DESTDIR"] = f"{tmpdir.name}/install/"
    check_call([MESON, 'compile'], env=env)


shared_objects = set()
class my_bdist_wheel(bdist_wheel):
    def run(self):
        # Extract libxml2's tarball to a temporary directory
        tmpdir = tempfile.TemporaryDirectory(prefix='python-libxml2.', delete=delete)
        url = mirror + f"/{major}.{minor}/libxml2-{version}.tar.xz"
        filename, message = urlretrieve(url, os.path.join(tmpdir.name, f"libxml2-{version}.tar.xz"))
        with tarfile.open(filename, 'r:xz') as f:
            f.extractall(tmpdir.name, filter='data')

        # Clean up parts of the temporary directory and make its path predictable
        os.unlink(os.path.join(tmpdir.name, f"libxml2-{version}.tar.xz"))
        os.rename(os.path.join(tmpdir.name, f"libxml2-{version}"), os.path.join(tmpdir.name, "src"))

        # Locate the headers -- this uses the exact same code as setup.py.in in libxml2's python/ folder
        def missing(file):
            if os.access(file, os.R_OK) == 0:
                return 1
            return 0

        ROOT = "/"
        try:
            HOME = os.environ['HOME']
        except:
            HOME="C:"

        includes_dir = [
            "/usr/include",
            "/usr/local/include",
            "/opt/include",
            os.path.join(ROOT, 'include'),
            HOME
        ]
        xml_includes=""
        for dir in includes_dir:
            if not missing(dir + "/libxml2/libxml/tree.h"):
                xml_includes=dir + "/libxml2"
                break;
        if xml_includes == "":
            print("failed to find headers for libxml2: update includes_dir")
            sys.exit(1)

        # Find out the options originally used when compiling libxml2
        CC = os.environ.get('CC', 'cc')
        data = check_output(
            [CC, '-w', '-I', xml_includes, '-E', '-ansi', '-P', str(Path(__file__).parent / 'libxml2-config.h')],
            text=True,
        )
        libxml2 = tomllib.loads(data)
        cversion = libxml2['config']['version']
        if cversion != version:
            raise ValueError(f"Incompatible versions: C library is {cversion} while the Python library expects {version}")

        # Patch the code to support Python >= 3.9.0
        # See https://sources.debian.org/patches/libxml2/2.12.7+dfsg+really2.9.14-2.1/python3.13.patch/
        # for more information.
        python_libxml_c = Path(tmpdir.name) / "src" / "python" / "libxml.c"
        python_libxml_c.write_bytes(
            python_libxml_c.read_bytes()
            .replace(b'PyEval_CallMethod', b'PyObject_CallMethod')
            .replace(b'PyEval_CallObject', b'PyObject_CallObject')
        )

        # Build libxml2 and install it inside temporary directory
        try:
            # libxml2 >= 2.13.0 uses meson for its compilation
            if major > 2 or (major == 2 and minor >= 13):
                build_using_meson(libxml2, tmpdir)
            else:
                build_using_autotools(libxml2, tmpdir)
        finally:
            os.chdir(old_pwd)

        # Move the newly-built files to this package's build directory.
        # We have to iterate over both "platlib" & "purelib" as they may be
        # different directories (e.g. "lib64" vs "lib" on Fedora).
        purelib = Path(tmpdir.name) / "install" / f"./{sysconfig.get_path('purelib')}"
        platlib = Path(tmpdir.name) / "install" / f"./{sysconfig.get_path('platlib')}"
        for d in (purelib, platlib):
            for f in d.iterdir():
                if not str(f).endswith((".so", ".py")):
                    continue
                new_path = Path(self.bdist_dir) / f.name
                new_path.parent.mkdir(parents=True, exist_ok=True)
                print(f"Moving '{f}' to '{new_path}'")
                shutil.move(str(f), str(new_path))
        bdist_wheel.run(self)


# Remove every file inside this package's "lib" folder except .gitignore
for root, dirs, files in (Path(__file__).parent / "lib").walk(top_down=False):
    for name in files:
        if (root / name) != (Path(__file__).parent / "lib" / ".gitignore"):
            (root / name).unlink()
    for name in dirs:
        (root / name).rmdir()


# Define the wrapper
setup(
    cmdclass={
        "bdist_wheel": my_bdist_wheel,
    },
    name="libxml2",
    version=version,
    description="A wrapper around the C libxml2 library to make it installable through pip/uv",
    url="https://github.com/fpoirotte/python-libxml2",
    #packages=[''],
    #package_dir={'': 'lib'},
    #package_data={'': list(shared_objects)},
    include_package_data=True,
)

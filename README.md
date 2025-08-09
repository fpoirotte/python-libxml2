# Python libxml2 wrapper

This repository acts as a wrapper around the C "libxml2" library and makes it easy to install through pip/uv.

**Note:** this repository is not related to the [official libxml2 repository](https://gitlab.gnome.org/GNOME/libxml2) in any way.
Please do not direct bug reports / questions related to this Python wrapper to the official repository so as not to burden the official maintainers.
See below for more information.

**Warning:** this wrapper has only been tested on Debian.
It might work on other distributions, but no guarantee is made.


## Why?

I was working on a project involving the `virt-install` command, which itself relies on the libxml2 python library to work.
I wanted to use [uv](https://docs.astral.sh/uv/) to track my project's dependencies.
Unfortunately, libxml2 is not distributed through PyPI, making its declaration inside uv impossible.

I thought maybe I could create a thin wrapper around the official libxml2 C library to make it possible.

I saw similar attempts in the past but it seems they were largely outdated (the latest release I found contained libxml2 2.4.x ...).
In addition, other packages I found could not be audited / rebuilt from source.
Hopefully, this repository should be small enough that it is easy to audit if necessary.

## Installation

### Using uv

```sh
uv add libxml2==2.9.14
```

**Note:** the version you install **MUST** match the version of libxml2 that is installed on your system.
Attempting to use any other version will fail during this module's compilation.

**Warning:** this will download and install a precompiled release.
If you are concerned about security (as you should), you can instead opt to install the module from sources.

### Using pip

Installation using pip should be similar to uv, but this has not been tested.

### From sources

#### Requirements

You will need the following packages to build the libxml2 Python library from sources:

* A working installation of Python >= 3.11
* autoconf
* A working compiler. GCC 14.2.0 is known to work.
* both the libxml2 C library and its header files (i.e. `libxml2` & `libxml2-dev` on Debian)
* header files for your Python installation (i.e. `python3-dev`)

**Note:** for now, only builds on Linux (Debian Trixie) have been tested.
Also, please note that as of this writing, the libxml2 package in Debian Trixie is `2.12.7+dfsg+really2.9.14-2.1`.
As the name suggests, this is actually libxml2 version 2.9.14 with many patches to make it look like libxml2 version 2.12.7.

##### Procedure

```sh
uv add "git+https://github.com/fpoirotte/python-libxml2" --branch 2.9.14
```

**Note:** the versioned branches contain the exact same code as the main branch, plus an additional commit to set the version.
These branches may be force-pushed to, to periodically rebase them on the latest code from the main branch.

## Bug reports

Please direct bug reports & questions related to this wrapper at <https://github.com/fpoirotte/python-libxml2/issues>.

## Credits

The official libxml2 C library has been created by [Daniel Veillard](http://veillard.com/).
It is now being maintained within the GNOME project.

## License

This code and accompanying files are released under the same license as libxml2 itself, namely the MIT license.
See `LICENSE` inside this repository for more information.

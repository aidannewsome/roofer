# Python bindings for roofer C++ API
We use pybind11 for python bindings. To use the bindings, build with either Conan or Nix.

With Conan:

```
cd roofer-dev
conan profile detect --force
conan install . \
  --output-folder=build_python \
  --build=missing \
  --settings=build_type=Release \
  --settings=compiler.cppstd=20 \
  --options="&:build_apps=False" \
  --options="&:use_spdlog=False" \
  --options="&:use_val3dity=False" \
  --options="&:build_bindings=True" \
  --options="&:build_testing=False"
cmake -S . -B build_python \
  -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE=build_python/conan_toolchain.cmake \
  -DCMAKE_BUILD_TYPE=Release \
  -DRF_BUILD_APPS=OFF \
  -DRF_USE_LOGGER_SPDLOG=OFF \
  -DRF_USE_VAL3DITY=OFF \
  -DRF_BUILD_BINDINGS=ON \
  -DRF_BUILD_TESTING=OFF \
  -DRF_USE_CPM=OFF
cmake --build build_python --target rooferpy
```

With Nix:

```
cd roofer-dev
nix develop
cmake -S . -B build_python \
  -G Ninja \
  -DRF_BUILD_APPS=OFF \
  -DRF_USE_LOGGER_SPDLOG=OFF \
  -DRF_USE_VAL3DITY=OFF \
  -DRF_BUILD_BINDINGS=ON \
  -DRF_BUILD_TESTING=OFF \
  -DRF_USE_CPM=OFF
cmake --build build_python --target rooferpy
```

The rooferpy library will be located in `build_python/rooferpy/roofer.cpython-<version-and-system>.so`. Import the .so file (e.g. place it in the same folder as .py script) to use roofer python API.

## Wheels

`pyproject.toml` in this folder builds the bindings as a wheel named `rooferpy`
(`roofer` is taken on PyPI by an unrelated project). The module is still
imported as `roofer`. The dependencies are found the same way as above, so give
CMake the Conan toolchain, or build inside `nix develop`:

```
pip wheel ./rooferpy --config-settings=cmake.define.CMAKE_TOOLCHAIN_FILE=$PWD/build_python/conan_toolchain.cmake
```

Wheels for every supported CPython, free-threaded 3.14t included, are built
with cibuildwheel, which runs the Conan install itself and tests each wheel
with `rooferpy/tests`:

```
pipx run cibuildwheel rooferpy
```

The dependencies are linked statically, so the wheels need nothing else
installed. The GitHub workflow `rooferpy-wheels.yml` builds them for Linux
x86_64 and macOS arm64, and publishes them to PyPI when a release is published.

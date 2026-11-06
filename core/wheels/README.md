# Pinned toolchain: fetch, verify, install

The answer key was produced under `ampliphi 1.0.0` (compiler) and `varphi-python 2.0.6`
(runtime), Python 3.13. The wheels are not redistributed here: both packages are
published on PyPI without a licence, and redistribution waits on their creators'
written permission (`LICENSE-DATA.md`). Fetch the exact releases from PyPI and verify
them against the hashes recorded in `../seeds-and-hashes.md`:

    pip download ampliphi==1.0.0 varphi-python==2.0.6 --no-deps --only-binary=:all: -d .
    sha256sum -c SHA256SUMS
    pip install ./*.whl

`SHA256SUMS` lists the two expected digests. On 6 November 2026 the PyPI downloads were
byte-identical to the copies this kit briefly vendored (63,584 and 8,576 bytes). Read
the Toolchain section of `../REPRODUCE.md` before substituting any newer version.

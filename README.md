WCS Downloader
==============

Downloads all coverages (image files) from a [WCS 2.0.1](https://www.ogc.org/standard/wcs/) service.

`wcs-download` fetches the service's capabilities, finds every coverage listed there, and downloads each one with a `GetCoverage` request into a local directory.

Setup
-----

```
pip install wcs-downloader                                       # soon
pip install git+https://github.com/codeforberlin/wcs-downloader  # directly from GitHub
```

Usage
-----

```
wcs-download URL [-o OUTPUT_PATH] [-s PATTERN/REPLACEMENT ...]
```

| Option                | Default  | Description                                                    |
| --------------------- | -------- | -------------------------------------------------------------- |
| `URL`                 |          | Base URL of the WCS service, without query parameters.         |
| `-o`, `--output-path` | `images` | Directory for the downloaded files. Created if it is missing.  |
| `-s`, `--substitute`  |          | One or more `pattern/replacement` rules to rename the files.   |

Examples:

```
# download everything into ./images
wcs-download https://example.com/path/to/wcs

# download into ./tiles instead
wcs-download https://example.com/path/to/wcs -o tiles

# strip a prefix from every file name and use .tiff as extension
wcs-download https://example.com/path/to/wcs -s '^dop20_/' '\.tif$/.tiff'
```

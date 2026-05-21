# hb-async-utils

[![CI](https://github.com/MementoRC/hb-async-utils/actions/workflows/ci.yml/badge.svg)](https://github.com/MementoRC/hb-async-utils/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/MementoRC/hb-async-utils)](https://codecov.io/gh/MementoRC/hb-async-utils)
[![PyPI version](https://badge.fury.io/py/hb-async-utils.svg)](https://badge.fury.io/py/hb-async-utils)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Async utility helpers and primitives for Hummingbot sub-packages.

> **Scaffolding note**: This repository has been initialized with the canonical hb-* package
> layout. Source implementation is pending migration from hummingbot core.

## Overview

This package provides async utility primitives used across Hummingbot sub-packages. It operates
as a standalone library and is a drop-in replacement for inlined async helpers in Hummingbot core.

## Installation

```bash
pip install hb-async-utils
```

Or with pixi:

```bash
pixi add hb-async-utils
```

## Usage

```python
import async_utils
```

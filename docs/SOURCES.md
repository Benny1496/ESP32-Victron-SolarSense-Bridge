# Sources and project structure (English)

[Deutsch](SOURCES.de.md) · [English](SOURCES.md) · [Documentation](README.md)

Detailed upstream author credits, provenance, licensing boundaries, and third-party rights appear in [Credits](CREDITS.en.md), with a German version at [CREDITS.de.md](CREDITS.de.md).

## What do the folders contain?

- **`esphome/`:** current public two-sensor template, adapted from privately live-tested stage 4.3.1. It includes the ESPHome configuration and the HTTPS background worker.
- **`src/`, `tests/test_solarsense.cpp`, `examples/`:** earlier independent prototypes and synthetic tests for decoding and variable sensor registries. These are **not** the same implementation as the current two-sensor ESPHome installation template.
- **`tests/test_duplicate.cpp`:** isolated forwarding and periodic-refresh decision test.
- **`docs/`:** guides in German and English. The [bilingual homepage](../README.md) summarizes the current source.

The original English-only prototype `README.md` was replaced with an up-to-date **German-English** homepage on 15 October 2026. The original text is preserved under [PROTOTYPE.en.md](PROTOTYPE.en.md), with a German translation at [PROTOTYPE.de.md](PROTOTYPE.de.md). The full firmware compiled successfully in GitHub Actions; the new TLS and duplicate-suppression features have not yet been integration-tested together on actual Cerbo hardware.

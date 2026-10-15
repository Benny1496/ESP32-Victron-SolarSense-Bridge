# Publication and privacy (English)

## What has been checked

The current `main` source was examined for real private LAN IPs, hardware MACs, private keys and known production configuration values. ESPHome configuration validation and isolated C++ tests also run in GitHub Actions. `scripts/check_publication_privacy.py` checks future commits for common accidental disclosures. **This heuristic is not a guarantee**: unknown secret formats may escape detection.

The original live stage 4.3.1 firmware is **not distributed unchanged**. Publishable files under `esphome/` use private `secrets.yaml` configuration and a user-supplied trusted TLS certificate. Two SolarSense sensors are the documented reference. Certificate-verified HTTPS and the 15-second duplicate refresh are new changes **not yet tested together on the production hardware**.

## Why not simply select Public?

The existing private Git history contains the abandoned Alpha branch and a closed pull request. Older revisions mention owner-specific device/testing context. Deleting files or branches does not necessarily remove prior commits and pull-request references. **Do not make the existing history public directly.**

## Clean publication path

1. Export the current `main` as **working-tree source files without the .git folder or any history**, e.g. GitHub's Download ZIP followed by extraction. Never upload the original unsanitized 4.3.1 ZIP.
2. Create a **new empty GitHub repository** using the intended public project name. **Do not fork the old repository, import Git history, or include the Alpha branch**. Retain the old repository as a private archive.
3. Copy the reviewed source files as a clean initial commit. Preserve the English `README.md` unchanged as requested, with `README.de.md` providing a German entry point.
4. Run privacy checks and GitHub Actions in the fresh repository. Describe the source honestly as a community preview with outstanding hardware verification.
5. The repository owner decides separately when to change its visibility to `Public`. Never include personal credentials, local certificates or firmware dumps.

**Note:** A clean history does not eliminate the need to review published file contents. Attribution and license information are in [CREDITS.en.md](CREDITS.en.md) and [LICENSE.en.md](LICENSE.en.md). An isolated compilation does not prove operation with a real Cerbo GX.

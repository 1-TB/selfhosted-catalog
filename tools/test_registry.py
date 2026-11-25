#!/usr/bin/env python3
"""Offline tests for the tag picking in registry.py.

  python3 -m unittest discover -s tools

`latest()` is tested against canned tag lists, so this needs no network.
"""

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import registry


def latest(tags):
    with mock.patch.object(registry, "tags", return_value=tags):
        return registry.latest("example.org/some/image")


class Latest(unittest.TestCase):
    def test_skips_short_beta_markers(self):
        # AdGuard Home publishes `-b.N` betas next to its stable releases.
        self.assertEqual(
            latest(["v0.107.80", "v1.0.0", "v1.0.0-b.2", "v1.1.0-b.1", "latest"]),
            "v1.0.0",
        )

    def test_skips_alpha_marker_without_dot(self):
        self.assertEqual(latest(["2.0.0-a3", "1.9.4"]), "1.9.4")

    def test_skips_next_prereleases(self):
        # Castopod's `-next.N` builds precede each major.
        self.assertEqual(latest(["1.15.5", "2.0.0-next.1", "2.0.0-next.2"]), "1.15.5")

    def test_skips_pre_and_rc(self):
        self.assertEqual(
            latest(["4.5.2", "4.6.0-pre.1", "5.7.0-pre0", "4.6.0-rc.1", "4.6.0-beta"]),
            "4.5.2",
        )

    def test_keeps_commit_hash_suffix(self):
        # IT Tools tags its releases `<date>-<short sha>`; a hash starting with
        # `a` or `b` must not read as an alpha or beta marker.
        self.assertEqual(latest(["2024.5.13-a0bc346", "2023.12.21-5ed3693"]), "2024.5.13-a0bc346")
        # A hash can also be `a` or `b` followed by nothing but digits.
        self.assertEqual(latest(["2024.5.13-a123456", "2023.12.21-5ed3693"]), "2024.5.13-a123456")
        self.assertEqual(latest(["2024.5.13-b9876543", "2023.12.21-5ed3693"]), "2024.5.13-b9876543")

    def test_keeps_variant_suffixes(self):
        self.assertEqual(latest(["1.20.0-ls123", "1.19.0"]), "1.20.0-ls123")
        self.assertEqual(latest(["7.1.15-php8.2-apache", "7.1.14-php8.2-apache"]), "7.1.15-php8.2-apache")

    def test_does_not_mistake_words_for_markers(self):
        # `next` and `b` only count as markers on their own.
        self.assertEqual(latest(["3.1.0-bookworm", "3.0.0"]), "3.1.0-bookworm")
        self.assertEqual(latest(["2.2.0-nextcloud", "2.1.0"]), "2.2.0-nextcloud")

    def test_prefers_exact_tag_over_floating(self):
        self.assertEqual(latest(["v2.16", "v2.16.0", "v2.15.3"]), "v2.16.0")

    def test_calver_only_repositories(self):
        self.assertEqual(latest(["260728", "261029", "latest"]), "261029")

    def test_semver_beats_calver(self):
        self.assertEqual(latest(["260728", "1.2.3"]), "1.2.3")

    def test_unpadded_calendar_release_is_kept(self):
        # authentik-style 2026.10.1 is a release; a padded date stamp is not.
        self.assertEqual(latest(["2026.10.1", "2026.10.01", "2026.8.3"]), "2026.10.1")

    def test_nothing_pinnable(self):
        self.assertIsNone(latest(["latest", "stable", "dev", "sha-0123abc"]))


if __name__ == "__main__":
    unittest.main()

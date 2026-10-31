import hashlib
import pathlib
import runpy
import tempfile
import unittest

module = runpy.run_path(str(pathlib.Path(__file__).with_name("verify-site.py")))
verify = module["verify"]
FILES = module["FILES"]


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        lines = []
        for name in sorted(FILES):
            file = self.root / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(name.encode())
            lines.append(f"{hashlib.sha256(file.read_bytes()).hexdigest()}  {name}\n")
        (self.root / "SHA256SUMS").write_text("".join(lines))

    def test_valid_artifact(self):
        verify(self.root)

    def test_modified_asset(self):
        (self.root / "index.html").write_text("changed")
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            verify(self.root)

    def test_extra_file(self):
        (self.root / "secret.txt").write_text("not public")
        with self.assertRaisesRegex(ValueError, "Unexpected or missing"):
            verify(self.root)

    def test_traversal_in_manifest(self):
        with (self.root / "SHA256SUMS").open("a") as manifest:
            manifest.write("0" * 64 + "  ../outside\n")
        with self.assertRaisesRegex(ValueError, "Unexpected or duplicate"):
            verify(self.root)

    def test_symlink(self):
        (self.root / "extra").symlink_to(self.root / "index.html")
        with self.assertRaisesRegex(ValueError, "Symlinks"):
            verify(self.root)


if __name__ == "__main__":
    unittest.main()

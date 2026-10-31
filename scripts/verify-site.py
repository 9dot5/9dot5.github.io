import argparse
import hashlib
import pathlib
import time
import urllib.request

FILES = {
    "index.html", "cv-en.pdf", "cv-pt.pdf", "css/main.css",
    "js/bootstrap.bundle.min.js", "img/ist-logo.png", "img/profile.png", ".nojekyll",
}


def verify(root, url=None):
    manifest = root / "SHA256SUMS"
    if manifest.is_symlink():
        raise ValueError("Manifest must not be a symlink")
    entries = {}
    for line in manifest.read_text().splitlines():
        digest, name = line.split("  ", 1)
        if name not in FILES or name in entries:
            raise ValueError(f"Unexpected or duplicate manifest entry: {name}")
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError(f"Invalid digest: {name}")
        entries[name] = digest
    if set(entries) != FILES:
        raise ValueError("Incomplete manifest")
    actual = set()
    for file in root.rglob("*"):
        if file.is_symlink():
            raise ValueError(f"Symlinks are not allowed: {file}")
        if file.is_file():
            actual.add(file.relative_to(root).as_posix())
    if actual != FILES | {"SHA256SUMS"}:
        raise ValueError("Unexpected or missing artifact files")
    for name, digest in entries.items():
        local = (root / name).read_bytes()
        if hashlib.sha256(local).hexdigest() != digest:
            raise ValueError(f"Local checksum mismatch: {name}")
        if url and not name.startswith('.'):
            for attempt in range(3):
                try:
                    request = urllib.request.Request(url.rstrip("/") + "/" + name, headers={"Cache-Control": "no-cache"})
                    with urllib.request.urlopen(request, timeout=30) as response:
                        if hashlib.sha256(response.read()).hexdigest() != digest:
                            raise ValueError(f"Public checksum mismatch: {name}")
                    break
                except (OSError, ValueError):
                    if attempt == 2:
                        raise
                    time.sleep(3)
        print(f"OK {name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=pathlib.Path)
    parser.add_argument("--url")
    args = parser.parse_args()
    verify(args.directory, args.url)

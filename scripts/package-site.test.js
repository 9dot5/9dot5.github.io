const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const { packageSite, files } = require('./package-site');

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'portfolio-test-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  for (const file of files) {
    fs.mkdirSync(path.dirname(path.join(root, file)), { recursive: true });
    fs.writeFileSync(path.join(root, file), file === 'index.html' ? '<link href="css/main.css"><img src="img/profile.png">' : file);
  }
  return root;
}

test('packages only public assets with valid checksums and removes stale output', t => {
  const root = fixture(t);
  fs.writeFileSync(path.join(root, 'private.txt'), 'not public');
  const dist = packageSite(root);
  fs.writeFileSync(path.join(dist, 'stale.txt'), 'old');
  packageSite(root);
  assert.equal(fs.existsSync(path.join(dist, 'private.txt')), false);
  assert.equal(fs.existsSync(path.join(dist, 'stale.txt')), false);
  const manifest = fs.readFileSync(path.join(dist, 'SHA256SUMS'), 'utf8').trim().split('\n');
  assert.equal(manifest.length, files.length + 1);
  for (const line of manifest) {
    const [hash, file] = line.split('  ');
    assert.equal(hash, crypto.createHash('sha256').update(fs.readFileSync(path.join(dist, file))).digest('hex'));
  }
});

test('rejects missing assets', t => {
  const root = fixture(t);
  fs.unlinkSync(path.join(root, 'cv-en.pdf'));
  assert.throws(() => packageSite(root), /ENOENT/);
});

test('rejects references outside the published file list', t => {
  const root = fixture(t);
  fs.appendFileSync(path.join(root, 'index.html'), '<script src="missing.js"></script>');
  assert.throws(() => packageSite(root), /Unpackaged local reference/);
});

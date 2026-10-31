const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const files = ['index.html', 'cv-en.pdf', 'cv-pt.pdf', 'css/main.css', 'js/bootstrap.bundle.min.js', 'img/ist-logo.png', 'img/profile.png'];

function packageSite(root) {
  for (const file of files) {
    if (!fs.statSync(path.join(root, file)).isFile()) throw new Error(`Not a file: ${file}`);
  }
  const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  for (const match of html.matchAll(/(?:src|href)="([^"#]+)"/g)) {
    const target = match[1];
    if (/^(?:https?:|mailto:)/.test(target)) continue;
    if (!files.includes(target)) throw new Error(`Unpackaged local reference: ${target}`);
  }
  const dist = path.join(root, 'dist');
  fs.rmSync(dist, { recursive: true, force: true });
  fs.mkdirSync(dist);
  for (const file of files) {
    fs.mkdirSync(path.dirname(path.join(dist, file)), { recursive: true });
    fs.copyFileSync(path.join(root, file), path.join(dist, file));
  }
  fs.writeFileSync(path.join(dist, '.nojekyll'), '');
  const checksums = [...files, '.nojekyll'].map(file => {
    const hash = crypto.createHash('sha256').update(fs.readFileSync(path.join(dist, file))).digest('hex');
    return `${hash}  ${file}\n`;
  }).join('');
  fs.writeFileSync(path.join(dist, 'SHA256SUMS'), checksums);
  return dist;
}

if (require.main === module) packageSite(path.join(__dirname, '..'));
module.exports = { packageSite, files };

// Copy the Bootstrap JS bundle next to the site, since GitHub Pages serves the repo as is
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
fs.mkdirSync(path.join(root, 'js'), { recursive: true });
fs.copyFileSync(
  path.join(root, 'node_modules/bootstrap/dist/js/bootstrap.bundle.min.js'),
  path.join(root, 'js/bootstrap.bundle.min.js')
);

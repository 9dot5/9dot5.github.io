// Publish the dev branch to production (main, served by GitHub Pages).
// Run with: npm run deploy   (must be on the dev branch with a clean working tree)
const { execSync } = require('child_process');
const readline = require('readline');

const run = (cmd) => execSync(cmd, { stdio: 'inherit' });
const out = (cmd) => execSync(cmd, { encoding: 'utf8' }).trim();

function ask(question) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise((resolve) => rl.question(question, (answer) => { rl.close(); resolve(answer.trim().toLowerCase()); }));
}

(async () => {
  const branch = out('git rev-parse --abbrev-ref HEAD');
  if (branch !== 'dev') {
    console.error(`Deploy must run from the dev branch (you are on "${branch}"). Run: git checkout dev`);
    process.exit(1);
  }
  if (out('git status --porcelain')) {
    console.error('Uncommitted changes on dev. Commit them first (the pre-commit hook rebuilds the CSS).');
    process.exit(1);
  }

  const answer = await ask('Publish dev to production (main -> https://9dot5.github.io)? [yes/no] ');
  if (!['yes', 'y', 'sim', 's'].includes(answer)) {
    console.log('Deploy cancelled.');
    process.exit(0);
  }

  run('npm run build --silent');
  try {
    run('git checkout main');
    run('git merge --no-ff dev -m "Deploy: merge dev into main"');
    run('git push origin main');
    console.log('\nDeployed. GitHub Pages will publish main in a minute or two.');
  } finally {
    run('git checkout dev');
  }
})().catch((err) => {
  console.error(err.message);
  process.exit(1);
});

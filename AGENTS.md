# Project commands and deployment constraints

- Use the Node version in `.node-version` and Python 3.11 or newer.
- Install JavaScript dependencies with `npm ci`; run `npm test` and `npm run build`.
- `npm run build` produces the public-only `dist/` artifact and its `SHA256SUMS`. Do not publish the repository root.
- `npm run serve` serves `dist/` on loopback port 8000. Rebuild after edits to refresh the preview.
- On Sigma, npm's default cache on AFS can fail with EXDEV hardlink errors. Set `npm_config_cache` to a private directory created with `mktemp -d /tmp/portfolio-npm-XXXXXXXX`.
- If Node 22 is not installed, use `npm exec --yes --package=node@22.23.4 --package=npm@10.9.3 --call 'npm ci && npm test && npm run build'` with that temporary cache.
- Local Ansible setup on Sigma: `python3 -m venv --without-pip --copies .venv`, then `python3 -m pip --python .venv/bin/python install --no-cache-dir -r deploy/requirements.txt`. The system lacks ensurepip; no sudo or global Python changes are needed.
- Validate Ansible with `.venv/bin/ansible-playbook -i localhost, deploy/tecnico.yml --syntax-check`. Run the isolated integration test with `.venv/bin/python scripts/integration-deploy.py`.
- Workflow `.github/workflows/deploy.yml` builds and tests pull requests, and deploys main to GitHub Pages. GitHub Pages must use the GitHub Actions source, rather than legacy branch publication, before activation.
- Find successful releases with `gh run list --repo 9dot5/9dot5.github.io --workflow deploy.yml --branch main --status success`.
- Publish the same release to Tecnico with `npm run deploy:tecnico -- -e run_id=RUN_ID`, from an authenticated Sigma session. Artifact retention is 30 days.
- The playbook requires a valid Kerberos ticket, refreshes AFS access with aklog, downloads the selected successful main workflow artifact, validates its allowlisted paths and checksums, requires its public assets to match the live GitHub Pages site before writing, and verifies Tecnico HTTP content after copying. It does not store credentials or renew tickets.
- If authentication has expired, run `kinit ist178938@IST.UTL.PT` interactively. The ticket inspected during setup was not renewable; do not assume automatic renewal is available.
- The publication directory is `/afs/.ist.utl.pt/users/3/8/ist178938/web`. Existing coursework directories must be preserved: never use a deployment-wide delete or rsync --delete there. Only the portfolio files listed in the playbook are managed.
- Assets are copied before index.html, but the entire site update is not atomic. GitHub Pages and Tecnico publication are separate operations and are not simultaneous.
- No Tecnico secret is required in GitHub for this local-deployment design. Do not read, copy, or commit credential caches or keytabs.
- Do not commit, push, or change GitHub Pages settings without explicit user authorization.

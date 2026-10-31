import functools
import hashlib
import http.server
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import threading

ROOT = pathlib.Path(__file__).resolve().parent.parent


def run():
    with tempfile.TemporaryDirectory(prefix="portfolio-integration-") as temp:
        temp = pathlib.Path(temp)
        web = temp / "web"
        web.mkdir()
        (web / "coursework").mkdir()
        (web / "coursework" / "old.txt").write_text("preserve")
        (web / "unmanaged.txt").write_text("preserve")
        binaries = temp / "bin"
        binaries.mkdir()
        sha = "a" * 40
        metadata = dict(status="completed", conclusion="success", headBranch="main", headSha=sha, event="push", workflowName="Deploy portfolio")
        shim = (
            "#!" + str(ROOT / ".venv/bin/python") + "\n"
            "import sys,pathlib,shutil,json\n"
            f"metadata = {metadata!r}\n"
            "if sys.argv[1:3] == ['run','view']:\n"
            " print(json.dumps(metadata))\n"
            "elif sys.argv[1:3] == ['run','download']:\n"
            " target = pathlib.Path(sys.argv[sys.argv.index('--dir')+1])\n"
            f" shutil.copytree({str(ROOT / 'dist')!r}, target, dirs_exist_ok=True)\n"
            "else:\n"
            " raise SystemExit(1)\n"
        )
        for name, contents in {"gh": shim, "klist": "#!/bin/sh\nexit ${PORTFOLIO_TEST_KLIST_RC:-0}\n", "aklog": "#!/bin/sh\nexit 0\n"}.items():
            file = binaries / name
            file.write_text(contents)
            file.chmod(0o700)
        shutil.copytree(ROOT / "dist", temp / "pages")
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(temp))
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            env = dict(os.environ, PATH=str(binaries) + os.pathsep + os.environ["PATH"], ANSIBLE_LOCAL_TEMP=str(temp / "ansible"), ANSIBLE_REMOTE_TEMP=str(temp / "remote"))
            command = [str(ROOT / ".venv/bin/ansible-playbook"), "-i", "localhost,", str(ROOT / "deploy/tecnico.yml"), "-e", json.dumps(dict(run_id="123", web_root=str(web), public_url=f"http://127.0.0.1:{server.server_port}/web/", pages_url=f"http://127.0.0.1:{server.server_port}/pages/"))]
            for _ in range(2):
                result = subprocess.run(command, env=env, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                if result.returncode:
                    print(result.stdout)
                    result.check_returncode()
                for source in (ROOT / "dist").rglob("*"):
                    if source.is_file():
                        published = web / source.relative_to(ROOT / "dist")
                        assert hashlib.sha256(published.read_bytes()).digest() == hashlib.sha256(source.read_bytes()).digest()
                assert (web / "coursework/old.txt").read_text() == "preserve"
                assert (web / "unmanaged.txt").read_text() == "preserve"
            expired = subprocess.run(command, env=dict(env, PORTFOLIO_TEST_KLIST_RC="1"), cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            assert expired.returncode != 0 and "Run kinit" in expired.stdout, expired.stdout
            (web / "index.html").unlink()
            (web / "index.html").symlink_to(web / "unmanaged.txt")
            rejected = subprocess.run(command, env=env, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            assert rejected.returncode != 0 and "Refusing to overwrite a symlink" in rejected.stdout, rejected.stdout
            assert (web / "unmanaged.txt").read_text() == "preserve"
            print("Integration OK: repeated deployment, public checksums, preserved projects, expired-ticket and symlink rejection")
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    run()

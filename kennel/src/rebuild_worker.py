# kennel/src/rebuild_worker.py
import subprocess
import time
import os

from rebuild_jobs import RebuildJob, RebuildStatus, rebuild_store
from flavours import FLAVOURS


PROVISION_DIR = "/opt/kennel/provision"


# ── Low-level helpers ─────────────────────────────────────────────────────────

def _run(cmd: list[str], job: RebuildJob, timeout: int = 900) -> bool:
    """Run a subprocess, streaming output line-by-line to the job log."""
    job.append_log(f"$ {' '.join(cmd)}")
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        for line in proc.stdout:
            job.append_log(line.rstrip())
        proc.wait(timeout=timeout)
        if proc.returncode != 0:
            job.append_log(f"[exit {proc.returncode}]")
            return False
        return True
    except subprocess.TimeoutExpired:
        proc.kill()
        job.append_log(f"[timeout after {timeout}s]")
        return False
    except Exception as e:
        job.append_log(f"[error: {e}]")
        return False


def _attach(container: str, script_path: str, job: RebuildJob, timeout: int = 1800) -> bool:
    """
    Pipe a provision script into the container via lxc-attach stdin, then run it.
    Using stdin avoids rootfs path issues with overlay-backed containers.
    """
    dest = f"/tmp/{os.path.basename(script_path)}"

    try:
        with open(script_path, "rb") as f:
            script_content = f.read()
    except Exception as e:
        job.append_log(f"[script read failed: {e}]")
        return False

    job.append_log(f"[inject] {os.path.basename(script_path)} → {dest}")
    try:
        write_proc = subprocess.run(
            ["lxc-attach", "-n", container, "--",
             "bash", "-c", f"cat > {dest} && chmod +x {dest}"],
            input=script_content,
            capture_output=True,
            timeout=30,
        )
        if write_proc.returncode != 0:
            job.append_log(f"[inject failed] {write_proc.stderr.decode().strip()}")
            return False
    except Exception as e:
        job.append_log(f"[inject error] {e}")
        return False

    return _run(
        ["lxc-attach", "-n", container, "--", "bash", dest],
        job,
        timeout=timeout,
    )


def _container_exists(name: str) -> bool:
    r = subprocess.run(["lxc-info", "-n", name], capture_output=True)
    return r.returncode == 0


def _container_running(name: str) -> bool:
    r = subprocess.run(
        ["lxc-info", "-n", name, "-s"],
        capture_output=True, text=True
    )
    return "RUNNING" in r.stdout


def _stop_container(name: str, job: RebuildJob) -> None:
    """Stop a container if it is running."""
    if _container_running(name):
        job.append_log(f"[stop] {name}")
        subprocess.run(["lxc-stop", "-n", name, "-k"], capture_output=True)


def _destroy_container(name: str, job: RebuildJob) -> None:
    """Stop and destroy a container unconditionally."""
    _stop_container(name, job)
    if _container_exists(name):
        job.append_log(f"[destroy] {name}")
        subprocess.run(["lxc-destroy", "-n", name, "-f"], capture_output=True)


# ── Overlay chain management ──────────────────────────────────────────────────

def _children_of(layer: str) -> list[str]:
    """Return the names of flavour layers that directly depend on this one."""
    return [
        name for name, defn in FLAVOURS.items()
        if defn.parent == layer
    ]


def _destroy_chain_from(layer: str, job: RebuildJob) -> None:
    """
    Recursively destroy base-{layer} and all overlay children.

    Overlay-backed containers share their parent's filesystem — destroying
    a parent while children still reference it corrupts them. Always destroy
    leaves first, then walk up toward the root.

    Note: user env containers (env-*) cloned from these bases are NOT
    tracked here. Running envs should be destroyed via DELETE /envs/{name}
    before forcing a parent layer rebuild.
    """
    for child in _children_of(layer):
        _destroy_chain_from(child, job)

    base = f"base-{layer}"
    if _container_exists(base):
        job.append_log(f"[chain] destroying {base}")
        _destroy_container(base, job)


def _list_user_envs() -> list[str]:
    result = subprocess.run(
        ["lxc-ls", "-1"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    return [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip().startswith("env-")
    ]


# ── Main worker ───────────────────────────────────────────────────────────────

def rebuild_flavour(job_id: str, flavour: str, force: bool = False) -> None:
    """
    Overlay chain build strategy:

      base-base   ← lxc-create from ubuntu template, run 00-base.sh in place
          │
          └─ lxc-copy -s -B overlay ─► base-dev   ← run 01-dev.sh in place
                                           │
                                           └─ lxc-copy -s -B overlay ─► base-cuda  ← run 02-cuda.sh in place

    Each base-{layer} container IS the layer — no build container, no promote
    step, no separate snapshot. User env spawning clones from the tip of the
    chain with another -s -B overlay, giving a fresh diff per workspace.

    Rebuilding a layer requires destroying all overlay children first (force).
    Without force, layers that already exist are skipped.
    """
    from flavours import build_order

    job            = rebuild_store.get(job_id)
    job.status     = RebuildStatus.running
    job.started_at = time.monotonic()

    try:
        chain = build_order(flavour)
        job.append_log(f"Build order: {' → '.join(chain)}")

        if force:
            user_envs = _list_user_envs()
            if user_envs:
                raise RuntimeError(
                    "force rebuild blocked while user env containers exist: "
                    + ", ".join(user_envs)
                    + ". Destroy them first to avoid breaking overlay ancestry."
                )

        for layer in chain:
            defn           = FLAVOURS[layer]
            base_container = f"base-{layer}"

            # ── Skip if already built ──────────────────────────────────────
            if not force and _container_exists(base_container):
                job.append_log(
                    f"[{layer}] {base_container} exists — skipping "
                    f"(pass force=true to rebuild)"
                )
                continue

            # ── With force: destroy this layer and all overlay dependents ──
            if force and _container_exists(base_container):
                job.append_log(
                    f"[{layer}] force=true — destroying {base_container} "
                    f"and all overlay dependents"
                )
                _destroy_chain_from(layer, job)

            job.append_log(f"\n{'─' * 50}")
            job.append_log(f"[{layer}] building layer")
            job.append_log(f"{'─' * 50}")

            # ── Create base container ──────────────────────────────────────
            if defn.parent is None:
                # Root layer — create from distro template directly
                job.append_log(
                    f"[{layer}] lxc-create from "
                    f"{defn.template}:{defn.release}"
                )
                ok = _run([
                    "lxc-create", "-n", base_container,
                    "-t", defn.template,
                    "--", "--release", defn.release,
                ], job, timeout=600)
            else:
                # Child layer — overlay clone of parent
                parent_container = f"base-{defn.parent}"
                if not _container_exists(parent_container):
                    raise RuntimeError(
                        f"Parent container {parent_container} not found — "
                        f"build {defn.parent} first"
                    )
                job.append_log(
                    f"[{layer}] overlay clone of {parent_container}"
                )
                ok = _run([
                    "lxc-copy",
                    "-n", parent_container,
                    "-N", base_container,
                    "-s",           # copy-on-write snapshot
                    "-B", "overlay",
                ], job, timeout=60)

            if not ok:
                raise RuntimeError(f"Container creation failed for {layer}")

            # ── Start ──────────────────────────────────────────────────────
            job.append_log(f"[{layer}] starting {base_container}")
            ok = _run(["lxc-start", "-n", base_container], job, timeout=30)
            if not ok:
                raise RuntimeError("lxc-start failed")

            time.sleep(3)   # let init settle before attaching

            # ── Run provision scripts ──────────────────────────────────────
            for script_name in defn.scripts:
                script_path = os.path.join(PROVISION_DIR, script_name)
                if not os.path.exists(script_path):
                    raise RuntimeError(f"Script not found: {script_path}")

                job.append_log(f"[{layer}] provisioning: {script_name}")
                ok = _attach(base_container, script_path, job, timeout=1800)
                if not ok:
                    raise RuntimeError(f"Provision script {script_name} failed")

            # ── Stop — layer is now ready for cloning ──────────────────────
            job.append_log(f"[{layer}] stopping {base_container}")
            _run(["lxc-stop", "-n", base_container], job, timeout=30)

            job.append_log(f"[{layer}] ✓ done — ready for overlay cloning")

        job.status   = RebuildStatus.done
        job.ended_at = time.monotonic()
        job.append_log(
            f"\n✓ Chain complete: {' → '.join(chain)}\n"
            f"  Spawn envs with: POST /envs {{\"flavour\": \"{flavour}\"}}"
        )

    except Exception as e:
        job.status   = RebuildStatus.failed
        job.ended_at = time.monotonic()
        job.error    = str(e)
        job.append_log(f"\n✗ Build failed: {e}")

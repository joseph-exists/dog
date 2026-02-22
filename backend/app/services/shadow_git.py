  # shadow_git.py - core operations

  def ensure_repo(repo_path: Path) -> None:
      """Initialize repo if it doesn't exist."""
      if not (repo_path / ".git").exists():
          repo_path.mkdir(parents=True, exist_ok=True)
          subprocess.run(["git", "init"], cwd=repo_path, check=True)

  def commit_snapshot(
      repo_path: Path,
      entity_type: str,
      snapshot_json: dict,
      message: str,
      author: str = "shadow-system"
  ) -> str:
      """Write snapshot to {entity_type}.json, commit, return SHA."""
      file_path = repo_path / f"{entity_type}.json"
      file_path.write_text(json.dumps(snapshot_json, indent=2))

      subprocess.run(["git", "add", file_path.name], cwd=repo_path, check=True)
      subprocess.run(
          ["git", "commit", "-m", message, "--author", f"{author} <{author}@shadow>"],
          cwd=repo_path, check=True
      )
      result = subprocess.run(
          ["git", "rev-parse", "HEAD"], cwd=repo_path, capture_output=True, text=True, check=True
      )
      return result.stdout.strip()

  def read_snapshot(repo_path: Path, entity_type: str, commit_sha: str) -> dict:
      """Read snapshot at specific commit."""
      result = subprocess.run(
          ["git", "show", f"{commit_sha}:{entity_type}.json"],
          cwd=repo_path, capture_output=True, text=True, check=True
      )
      return json.loads(result.stdout)

  def get_latest_commit(repo_path: Path) -> str | None:
      """Get HEAD commit SHA, or None if no commits."""
      result = subprocess.run(
          ["git", "rev-parse", "HEAD"], cwd=repo_path, capture_output=True, text=True
      )
      return result.stdout.strip() if result.returncode == 0 else None
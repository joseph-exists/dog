In Git, a **branch** and a **worktree** are related but distinct concepts:

- A **branch** is a lightweight pointer to a commit in your repository’s history. It represents a line of development (e.g., `main`, `feature/user-login`) and lives entirely inside `.git/refs/heads`. [stackoverflow](https://stackoverflow.com/questions/67995725/what-is-the-difference-between-a-new-working-tree-and-a-branch)
- A **worktree** (or working tree) is the actual directory of checked‑out files on disk that corresponds to whatever commit is represented by the currently checked‑out branch. By default, a repo has one worktree, but Git supports **multiple worktrees** tied to the same repository, each on a different branch. [git-scm](https://git-scm.com/docs/git-worktree)

### Key differences

- **Scope**:  
  - A branch is a *logical* line of commits in the repo.  
  - A worktree is the *physical* file tree you edit on your filesystem. [stackoverflow](https://stackoverflow.com/questions/67995725/what-is-the-difference-between-a-new-working-tree-and-a-branch)

- **Multiple worktrees**:  
  - With `git worktree add <path> <branch>`, you can have multiple directories (worktrees) for the same repo, each on a different branch.  
  - All worktrees share the same Git object database and branches, they just have separate working directories and indices. [williamdurand](https://williamdurand.fr/2021/05/05/an-introduction-to-git-worktree/)

- **Behavior during commits / changes**:  
  - Changes you make in one worktree are local to that directory’s index and head until committed and pushed.  
  - Commits still belong to the branch that is checked out in that worktree, so the *history* is the same whether you use a single worktree with frequent `checkout`s or multiple worktrees. [reddit](https://www.reddit.com/r/git/comments/ri0po2/longrunning_branches_and_git_worktree/)

In short:  
- **Branch** = pointer to a commit / line of development.  
- **Worktree** = the real‑world directory of files you see and edit, currently backed by that branch. [git-scm](https://git-scm.com/docs/git-worktree)
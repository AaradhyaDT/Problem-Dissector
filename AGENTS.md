# Agent Rules & Workflow Guidelines — Problem-Dissector

Welcome, Agent. This repository (`Problem-Dissector`) serves as the **Algorithmic Problem Dissector & Cognitive Deconstruction Engine for Competitive Programming** across IEEE-Xtreme, CS Academy, Codeforces, and LeetCode datasets.

---

## 1. Git Workflow & Ecosystem Automation (CRITICAL — STRICT ENFORCEMENT)

To avoid breaking branch tracking and prevent wasteful multi-step Git commands, **NEVER run individual `git add`, `git commit`, `git push`, or `git pull` commands directly.**

**ALWAYS execute `.\sync.bat` (or `.\sync.ps1`) for repository synchronization and version control.**
*(Note: `.\sync.bat` is the zero-friction execution wrapper that automatically bypasses PowerShell ExecutionPolicy restrictions).*

### Core Commands

- **Routine Sync**:
  ```powershell
  .\sync.bat
  ```
- **Major Features / Architectural Changes**:
  ```powershell
  .\sync.bat -m "feat(scope): detailed commit summary (#id)"
  ```
- **Pull Request Automation**:
  ```powershell
  .\sync.bat -PR -m "feat(scope): summary" -Issue 1
  ```
- **Safe Pull Only**:
  ```powershell
  .\sync.bat -PullOnly
  ```

---

## 2. Verification Gates & Reality Layer

Before finalizing changes or committing:
1. **Pytest Verification**:
   ```powershell
   pytest tests/ -v
   ```
   Ensure all unit tests pass with 100% pass rate.

2. **Zero Credential Commits**:
   Never commit `.env`, session files, cookies, or raw API tokens.

"""
Universal Atomic Dissector Engine (`atomic-dissector`).
Domain-agnostic specification analysis, invariant extraction, failure-mode analysis,
and deterministic contract emission across 4 foundational domains:
1. Competitive Programming & Algorithmic Complexity (CP)
2. Systems Architecture, Distributed State & Concurrency (SYSTEMS)
3. Edge AI, Microcontroller & Real-Time Kinematics (EDGE_AI)
4. Cyber Security, Privilege Boundaries & Forensics (SECURITY)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ProblemDomain(str, Enum):
    CP = "competitive_programming"
    SYSTEMS = "systems_architecture"
    EDGE_AI = "edge_ai_kinematics"
    SECURITY = "security_forensics"
    GENERAL = "general_engineering"


@dataclass
class AsymptoticContract:
    time_complexity_ceiling: str = "O(N)"
    space_complexity_ceiling: str = "O(N)"
    ops_budget: int = 100_000_000
    dominant_dimension: str = "N <= 1e5"
    memory_limit_mb: float = 256.0
    time_limit_ms: float = 1000.0


@dataclass
class FailureModeTrap:
    category: str
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    vulnerability_trigger: str
    mitigation_invariant: str


@dataclass
class UniversalDissectionContract:
    version: str = "2.0.0"
    task_slug: str = "unnamed_task"
    domain: ProblemDomain = ProblemDomain.GENERAL
    title: str = "Specification Dissection"
    asymptotics: AsymptoticContract = field(default_factory=AsymptoticContract)
    hard_invariants: list[str] = field(default_factory=list)
    failure_mode_traps: list[FailureModeTrap] = field(default_factory=list)
    forbidden_anti_patterns: list[str] = field(default_factory=list)
    recommended_tier: str = "balance"  # efficiency, balance, intelligence
    recommended_model_class: str = "copilot_cli"
    requires_cloud_burst: bool = False
    verification_matrix: list[str] = field(default_factory=list)
    agent_prompt_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["domain"] = self.domain.value
        return data


class UniversalDissector:
    """Zero-AI deterministic AST, keyword, and formal constraint analyzer."""

    def __init__(self, raw_text: str, task_slug: str = "task", domain: ProblemDomain | None = None):
        self.raw_text = raw_text
        self.task_slug = task_slug
        self.text_lower = raw_text.lower()
        self.domain = domain or self._detect_domain()

    def _detect_domain(self) -> ProblemDomain:
        scores = {
            ProblemDomain.CP: len(re.findall(r"\b(modulo|array|graph|tree|subtask|test case|testcase|standard input|standard output|constraints|transition table|10\^|dp|greedy|dijkstra|segment tree|cs academy|ieeextreme)\b", self.text_lower)),
            ProblemDomain.SYSTEMS: len(re.findall(r"\b(concurrency|thread|race condition|deadlock|mutex|asyncio|fastapi|wal|sqlite|worktree|dag)\b", self.text_lower)),
            ProblemDomain.EDGE_AI: len(re.findall(r"\b(tinyml|esp32|imu|gyro|accelerometer|sram|int8|quantization|freertos|cortex-m|200hz)\b", self.text_lower)),
            ProblemDomain.SECURITY: len(re.findall(r"\b(pe header|ads|alternate data stream|privilege|injection|sandbox|sha-256|exploit|rlo|forensic)\b", self.text_lower)),
        }
        best = max(scores, key=lambda k: scores[k])
        return best if scores[best] >= 2 else ProblemDomain.GENERAL

    def dissect(self) -> UniversalDissectionContract:
        contract = UniversalDissectionContract(
            task_slug=self.task_slug,
            domain=self.domain,
            title=f"Dissection Contract: {self.task_slug}"
        )

        if self.domain == ProblemDomain.CP:
            self._dissect_cp(contract)
        elif self.domain == ProblemDomain.SYSTEMS:
            self._dissect_systems(contract)
        elif self.domain == ProblemDomain.EDGE_AI:
            self._dissect_edge_ai(contract)
        elif self.domain == ProblemDomain.SECURITY:
            self._dissect_security(contract)
        else:
            self._dissect_general(contract)

        # Generate bounded agent prompt summary (< 500 chars)
        contract.agent_prompt_summary = (
            f"[{contract.domain.value.upper()}] Ceiling: {contract.asymptotics.time_complexity_ceiling}. "
            f"Tier: {contract.recommended_tier}. Cloud Burst: {contract.requires_cloud_burst}. "
            f"Invariants: {len(contract.hard_invariants)} extracted. "
            f"Traps: {len(contract.failure_mode_traps)} detected. "
            f"Zero-token contract ready for worker fleet execution."
        )
        return contract

    def _dissect_cp(self, contract: UniversalDissectionContract) -> None:
        contract.asymptotics.time_complexity_ceiling = "O(N log N) or O(N)"
        contract.asymptotics.space_complexity_ceiling = "O(N)"
        contract.asymptotics.ops_budget = 100_000_000
        contract.asymptotics.memory_limit_mb = 256.0
        contract.asymptotics.time_limit_ms = 1000.0

        # Check for automaton / transition table or Turing machine
        if any(kw in self.text_lower for kw in ["turing", "tape", "transition table", "transitions.tsv"]):
            contract.hard_invariants.append("Automaton/Turing Machine detected: inspect transitions for artificial busy-wait traps or ripple-carry counters before simulating.")
            contract.failure_mode_traps.append(FailureModeTrap(
                category="Anti-Simulation Busy-Wait Counter",
                risk_level="CRITICAL",
                vulnerability_trigger="Input > 30 branches into state cycle counting 2^30 steps",
                mitigation_invariant="Short-circuit state machine directly to terminal entry state after verifying output equivalency"
            ))
            contract.requires_cloud_burst = True

        if "modulo" in self.text_lower or re.search(r"\bmod\s+\d+", self.text_lower):
            contract.hard_invariants.append("Modular Arithmetic: perform subtraction as (a - b % M + M) % M and products via 64-bit casting.")
            contract.failure_mode_traps.append(FailureModeTrap(
                category="Negative Modulo / Integer Overflow",
                risk_level="HIGH",
                vulnerability_trigger="Multiplication before modulo overflows 32-bit int; signed negative remainder",
                mitigation_invariant="Cast to long long / uint64_t and add modulus before secondary mod"
            ))

        contract.recommended_tier = "balance" if not contract.requires_cloud_burst else "intelligence"
        contract.forbidden_anti_patterns.extend([
            "Raw unbuffered std::cin/std::cout without cin.tie(NULL)",
            "Recursive DFS without deep stack guard or recursion limit on tree depth >= 1e5",
            "Unordered map without custom SplitMix64 anti-collision hash"
        ])
        contract.verification_matrix.extend([
            "Sample cases 1..N exact match",
            "Anti-Quicksort / adversarial permutation stress test",
            "Hash collision flood test",
            "Maximum N boundary run within 1000 ms"
        ])

    def _dissect_systems(self, contract: UniversalDissectionContract) -> None:
        contract.asymptotics.time_complexity_ceiling = "Sub-100ms response / O(1) concurrent dispatch"
        contract.asymptotics.space_complexity_ceiling = "Bounded RAM (< 200 MB)"
        contract.asymptotics.ops_budget = 50_000_000

        contract.hard_invariants.append("Context Firebreak (INV-CTX-FIREBREAK): Zero main-thread conversational chatter; output <= 300w manifest.")
        contract.hard_invariants.append("Subprocess Isolation: Separate credentials, ports, and worktrees for all concurrent tasks.")

        if "sqlite" in self.text_lower or "db" in self.text_lower:
            contract.hard_invariants.append("Database Concurrency: WAL mode enabled; use busy_timeout >= 5000ms to prevent lock contention.")
            contract.failure_mode_traps.append(FailureModeTrap(
                category="SQLite Database Lock Timeout",
                risk_level="HIGH",
                vulnerability_trigger="Multi-process writes concurrently without WAL mode or retry loop",
                mitigation_invariant="Enforce PRAGMA journal_mode=WAL and PRAGMA busy_timeout=5000"
            ))

        contract.recommended_tier = "balance"
        contract.forbidden_anti_patterns.extend([
            "Headless interactive CLI prompts waiting on stdin",
            "Global mutable singleton state across concurrent worker threads",
            "Polling without backoff or reactive event wakeup"
        ])
        contract.verification_matrix.extend([
            "Multi-worker concurrency stress harness (stress_test_concurrency.py)",
            "Zero leaked process handles / background zombie check",
            "Crash-recovery state replay test"
        ])

    def _dissect_edge_ai(self, contract: UniversalDissectionContract) -> None:
        contract.asymptotics.time_complexity_ceiling = "200Hz loop (<= 5 ms per inference window)"
        contract.asymptotics.space_complexity_ceiling = "Sub-100KB INT8 flash, < 32KB SRAM tensor arena"
        contract.asymptotics.dominant_dimension = "T <= 200 samples per window, 6-axis IMU"

        contract.hard_invariants.append("Tensor Arena Constraint: TensorArena memory buffer must be statically allocated and cache-aligned.")
        contract.hard_invariants.append("INT8 Quantization: Quantize all weights and activations; zero floating-point operations in inner loop.")
        contract.hard_invariants.append("Safety Recall Invariant: True positive recall on critical state >= 0.95.")

        contract.failure_mode_traps.append(FailureModeTrap(
            category="Dynamic Allocation in Real-Time Loop",
            risk_level="CRITICAL",
            vulnerability_trigger="malloc() / new inside 200Hz sensor callback causing heap fragmentation and hard fault",
            mitigation_invariant="All buffers must be static or stack-allocated prior to timer initialization"
        ))

        contract.recommended_tier = "intelligence"
        contract.forbidden_anti_patterns.extend([
            "Dynamic memory allocation (malloc/calloc/free) in FreeRTOS tasks",
            "Floating point math on non-FPU microcontrollers",
            "Blocking delay (vTaskDelay) inside ISR interrupt routines"
        ])
        contract.verification_matrix.extend([
            "Tensor arena memory allocation boundary check",
            "Cycle count profiling under 5ms deadline",
            "Quantization clipping error regression test"
        ])

    def _dissect_security(self, contract: UniversalDissectionContract) -> None:
        contract.asymptotics.time_complexity_ceiling = "O(N) linear stream inspection"
        contract.asymptotics.space_complexity_ceiling = "O(1) streaming buffer"

        contract.hard_invariants.append("Zero-Trust Verification: All untrusted paths, PE headers, and payloads must be checked against canonical boundaries.")
        contract.hard_invariants.append("Chain of Custody: Record SHA-256 digests and UTC timestamps before and after inspection.")

        contract.failure_mode_traps.append(FailureModeTrap(
            category="Path Traversal / ADS Masquerade",
            risk_level="CRITICAL",
            vulnerability_trigger="Unsanitized filename with :$DATA stream or ..\\ sequence escaping sandbox",
            mitigation_invariant="Strictly validate Path.resolve() against root sandbox path and reject colons"
        ))

        contract.recommended_tier = "balance"
        contract.forbidden_anti_patterns.extend([
            "Raw subprocess shell=True execution with external strings",
            "Blind pickle/yaml deserialization of untrusted payloads",
            "Omitting SHA-256 validation on fetched binary blobs"
        ])
        contract.verification_matrix.extend([
            "Path traversal attack fuzzing",
            "PE header corruption fuzzing",
            "Alternate Data Stream detection test"
        ])

    def _dissect_general(self, contract: UniversalDissectionContract) -> None:
        contract.hard_invariants.append("Formal Specification Compliance: All changes must pass existing unit test suites without regressions.")
        contract.recommended_tier = "efficiency"
        contract.verification_matrix.append("Unit tests pass 100%")


def dissect_file(file_path: str, slug: str | None = None, domain: str | None = None) -> UniversalDissectionContract:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    raw_text = path.read_text(encoding="utf-8", errors="ignore")
    parsed_domain = ProblemDomain(domain) if domain and domain in ProblemDomain._value2member_map_ else None
    dissector = UniversalDissector(raw_text=raw_text, task_slug=slug or path.stem, domain=parsed_domain)
    return dissector.dissect()


def main():
    parser = argparse.ArgumentParser(description="Universal Atomic Dissector CLI (Problem-Dissector v2.0)")
    parser.add_argument("input", nargs="?", help="Path to specification, statement, or source file")
    parser.add_argument("--slug", "-s", help="Task slug identifier")
    parser.add_argument("--domain", "-d", choices=[d.value for d in ProblemDomain], help="Explicit problem domain")
    parser.add_argument("--output", "-o", help="Path to write output contract JSON")
    parser.add_argument("--contract", "-c", action="store_true", help="Print contract JSON to stdout")
    parser.add_argument("--quiet", "-q", action="store_true", help="Minimal stdout output")
    args = parser.parse_args()

    if not args.input:
        parser.print_help()
        sys.exit(1)

    contract = dissect_file(args.input, slug=args.slug, domain=args.domain)
    contract_json = json.dumps(contract.to_dict(), indent=2)

    if args.output:
        out_p = Path(args.output)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(contract_json, encoding="utf-8")
        if not args.quiet:
            print(f"[OK] Dissection contract exported to: {out_p}")

    if args.contract or not args.output:
        print(contract_json)


if __name__ == "__main__":
    main()

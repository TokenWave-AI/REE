"""Summarize Harbor runs on REE by system and area.

    python scripts/summarize.py jobs [more job folders]

For each system (agent and model) it reports, over the tasks it was scored on, the mean score
(100 times the reward: 0 = the starter, 100 = the problem's limit) and the mean score per area.
A trial that ended in an error other than the agent's time limit, such as an API error or a
container failure, is not counted; run the task again. When a task has more than one counted
trial, the earliest counts. Below the table, the paper's agents are scored on the same tasks.
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

AREAS = [
    ("Mathematics & Computing", "Math & Comp."),
    ("Physical Sciences & Engineering", "Phys. Sci. & Eng."),
    ("Life & Health Sciences", "Life & Health"),
    ("Earth & Environmental Sciences", "Earth & Env."),
    ("Language, Society & Culture", "Lang., Soc. & Culture"),
]
PAPER = Path(__file__).resolve().parent.parent / "results" / "paper-v1.tsv"
# The time limit ends a run normally; its last version is graded.
CLEAN_EXCEPTIONS = {None, "AgentTimeoutError"}


def reward_of(trial_dir, result):
    """The trial's reward, or None when the verifier wrote none."""
    rewards = (result.get("verifier_result") or {}).get("rewards") or {}
    if "reward" in rewards:
        return float(rewards["reward"])
    path = trial_dir / "verifier" / "reward.json"
    if path.exists():
        return float(json.loads(path.read_text())["reward"])
    return None


def load_trials(roots, known):
    """Yield (system, task, started_at, reward or None, errored) for every trial under the given folders."""
    for root in roots:
        for result_path in sorted(Path(root).rglob("result.json")):
            try:
                result = json.loads(result_path.read_text())
            except (OSError, ValueError):
                continue
            if not isinstance(result, dict) or "task_name" not in result:
                continue  # a job-level result.json, or a file of the same name inside a method
            info = result.get("agent_info") or {}
            agent = info.get("name") or result["config"]["agent"]["name"]
            model = (info.get("model_info") or {}).get("name") or result["config"]["agent"].get("model_name")
            system = f"{agent} / {model}" if model else agent
            task = result["task_name"].split("/")[-1]
            if task not in known:
                path = (result["config"].get("task") or {}).get("path")
                task = Path(path).name if path else task
            errored = (result.get("exception_info") or {}).get("exception_type") not in CLEAN_EXCEPTIONS
            # A trial without a start time sorts last, so it never displaces a dated one.
            started = result.get("started_at") or "~"
            yield system, task, started, reward_of(result_path.parent, result), errored


def row(scores, area):
    """scores: {task: score on 0-100} -> [tasks, mean, mean per area] as strings."""
    cells = [str(len(scores)), mean(scores.values())]
    for name, _ in AREAS:
        cells.append(mean([s for t, s in scores.items() if area.get(t) == name]))
    return cells


def mean(values):
    values = list(values)
    return f"{sum(values) / len(values):.1f}" if values else "-"


def print_table(rows):
    header = ["System", "Tasks", "Score"] + [short for _, short in AREAS]
    print("| " + " | ".join(header) + " |")
    print("|---|" + "--:|" * (len(header) - 1))
    for name, cells in rows:
        print("| " + " | ".join([name] + cells) + " |")


def main(roots):
    paper = list(csv.DictReader(PAPER.open(), delimiter="\t"))
    area = {r["task"]: r["area"] for r in paper}

    first = {}  # (system, task) -> (started_at, score) of the earliest counted trial
    errored = defaultdict(int)
    unscored = defaultdict(int)
    for system, task, started, reward, failed in load_trials(roots, area):
        if failed:
            errored[system] += 1
            continue
        if reward is None:
            unscored[system] += 1
            continue
        key = (system, task)
        score = 100 * min(1.0, max(0.0, reward))
        if key not in first or started < first[key][0]:
            first[key] = (started, score)

    by_system = defaultdict(dict)
    for (system, task), (_, score) in first.items():
        by_system[system][task] = score
    if not by_system:
        sys.exit("no counted trials found")

    print_table([(s, row(t, area)) for s, t in sorted(by_system.items())])
    for system, n in sorted(errored.items()):
        print(f"\n{system}: {n} trial(s) ended in an error (not the time limit), not counted; run them again.")
    for system, n in sorted(unscored.items()):
        print(f"\n{system}: {n} trial(s) without a reward, not counted.")
    unknown = sorted({t for tasks in by_system.values() for t in tasks if t not in area})
    if unknown:
        print(f"\nNot REE tasks, so not in the per-area columns: {', '.join(unknown)}")

    # The paper's agents, once for each distinct set of REE tasks the systems above were scored on.
    groups = defaultdict(list)
    for system, tasks in sorted(by_system.items()):
        ree = frozenset(t for t in tasks if t in area)
        if ree:
            groups[ree].append(system)
    for tasks, systems in groups.items():
        reference = defaultdict(dict)
        for r in paper:
            if r["task"] in tasks:
                reference[f'{r["agent"]} (paper)'][r["task"]] = float(r["score"])
        print(f"\nThe paper's agents on the {len(tasks)} task(s) of {', '.join(systems)}:\n")
        print_table([(s, row(t, area)) for s, t in reference.items()])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])

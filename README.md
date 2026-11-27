<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/brand/tokenwave-dark.svg">
    <img src="assets/brand/tokenwave.svg" alt="TokenWave" height="44">
  </picture>
</p>

# REE: A Scientific Research Entrance Exam for AI Agents

<p align="center">
  <a href="https://tokenwave-ai.github.io/REE/"><img src="assets/icons/tokenwave.svg" alt="" height="16" align="absmiddle"> Blog</a> ·
  <a href="https://arxiv.org/abs/2611.34646"><img src="assets/icons/arxiv.svg" alt="" height="16" align="absmiddle"> Paper</a> ·
  <a href="https://huggingface.co/datasets/Tokenwave-AI/REE"><img src="assets/icons/huggingface.svg" alt="" height="16" align="absmiddle"> Dataset</a> ·
  <a href="#quick-start">Quick start</a>
</p>

REE is a benchmark that tests AI agents on scientific research. Each of its 100 open-ended research problems, drawn from active research in its field and reviewed by domain experts, gives the agent a statement, a working starter solution and development data, and up to twelve hours to improve the solution on its own. Held-out test instances it never sees evaluate the result, on one scale from the starter solution (0) to the upper bound of the task's metric (100), and beside it an established human-designed solution to the same problem, the expert solution, evaluated on the same instances under comparable conditions.

The problems span 23 domains in five areas: Mathematics & Computing (20), Physical Sciences & Engineering (25), Life & Health Sciences (19), Earth & Environmental Sciences (12) and Language, Society & Culture (24).

This repository holds the Harbor configs of the agents we evaluated, the run prompt of our runs, a script to download the tasks, a script to summarize the results, and the project page (`docs/`). The tasks, with their graders, held-out test instances and expert solutions, are on [Hugging Face](https://huggingface.co/datasets/Tokenwave-AI/REE). Every task is a standard [Harbor](https://github.com/laude-institute/harbor) task directory.

## Results

Mean score on the 100 problems, one run per task (0 = the starter solution, 100 = the upper bound). *Margin* is the mean difference from the expert baseline on the same task, and *Win rate* the share of tasks with a positive margin.

| Agent | Harness | Score | Margin | Win rate | Math & Comp. | Phys. Sci. & Eng. | Life & Health | Earth & Env. | Lang., Soc. & Culture |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|
| Claude Opus 5.5 | Claude Code 2.1 | **39.6** | +15.2 | 86% | 47.1 | 40.0 | 36.5 | 34.8 | 38.0 |
| GPT-6.1 Sol | Codex CLI 0.154.0 | **38.2** | +13.8 | 81% | 45.7 | 37.8 | 36.5 | 30.0 | 38.0 |
| GLM-5.3 | Claude Code 2.1 | **28.6** | +4.2 | 67% | 32.0 | 30.5 | 27.2 | 21.1 | 28.9 |
| Grok 4.7 | Claude Code 2.1 | **25.3** | +0.9 | 61% | 28.0 | 27.1 | 24.2 | 22.2 | 23.7 |
| Expert baseline | | **24.4** | | | 35.3 | 21.8 | 20.9 | 14.7 | 25.9 |

Every agent ran at its highest reasoning effort with its maximum context window. The two leading agents score above the expert baseline on more than four tasks in five, and the scores still remain far from the upper bound: no run reaches it, and the highest final score on any task is 81.7. The agents' score on every task is in [`results/paper-v1.tsv`](results/paper-v1.tsv).

## Setup

You need a Linux x86-64 machine with Docker, Python 3.12 and two Python packages:

```bash
pip install harbor==0.23.0 "huggingface_hub>=1.0"
git clone https://github.com/TokenWave-AI/REE.git
cd REE
```

Harbor 0.23.0 is the version our runs used. Each task runs in two containers, one for the agent and one for grading. The agent's has 4 CPU cores, 16 GB of memory and 10 GB of disk; the grader's has 4 cores, 8 GB and 10 GB. Two tasks, `container_terminal` and `delivery_depot`, give the agent 8 cores and the grader 32 GB. All 100 tasks take 66.6 GiB. Building a task's images needs the network; the agent and the grader then run offline.

## Quick start

Fetch one small task and check it. The starter scores 0 and the expert solution 0.366 (36.6 on the scale of the tables).

```bash
scripts/fetch.sh seismic_observatory
harbor run -p REE/tasks/seismic_observatory -a nop -y -o jobs
harbor run -p REE/tasks/seismic_observatory -a oracle -y -o jobs
python scripts/summarize.py jobs
```

`fetch.sh` downloads the task from Hugging Face into `REE/tasks/` and restores the executable bits that Hugging Face does not store. It also takes an area (`math`, `physical`, `life`, `earth` or `language`) or `all`. Keep `task.toml` and the task's files as they are, since a changed task is not the task scored here.

The grader reruns the submitted solution on every held-out test instance under the time limits its statement sets, so a score depends on the CPU time a trial actually gets. Give each trial its own cores and run no more trials at once than the machine has free sets of four, for instance with `-n 1`.

## Running an agent

`configs/` holds one Harbor job config for each agent in the table, with the settings below. Run them from the repository root.

```bash
# Claude Opus 5.5 in Claude Code
export ANTHROPIC_API_KEY=...
harbor run -c configs/claude-opus-5-5.yaml -p REE/tasks/<task>

# GPT-6.1 Sol in Codex
unset CODEX_FORCE_AUTH_JSON CODEX_AUTH_JSON_PATH
export OPENAI_API_KEY=...
harbor run -c configs/gpt-6.1-sol.yaml -p REE/tasks/<task>
```

Pass `-p REE/tasks` to run every fetched task, and `-n` to run several at a time. Harbor writes the results to `jobs/`, and `python scripts/summarize.py jobs` turns them into mean scores overall and by area, beside the paper's agents on the same tasks. Add `--print-config` to see the full settings without running.

To use another endpoint, export its base URL and allow its host:

```bash
export ANTHROPIC_BASE_URL=https://gateway.example.com
harbor run -c configs/claude-opus-5-5.yaml -p REE/tasks --allow-agent-host gateway.example.com
```

Claude Code adds `/v1/messages` to its base URL, so give it the root of the endpoint. Codex adds `/responses`, so `OPENAI_BASE_URL` ends in `/v1`. The configs for GLM-5.3 and Grok 4.7 run those models in Claude Code, so they need an endpoint that serves them through the Anthropic Messages API.

To test another model, copy the closest config and change `model_name` and the two alias variables, `ANTHROPIC_DEFAULT_FABLE_MODEL` and `ANTHROPIC_SMALL_FAST_MODEL`. Set the model in the config. With `-c`, Harbor ignores `-m` unless `-a` is also given, and `-a` replaces the agent of the config.

| Setting | Claude Code | Codex CLI |
|---|---|---|
| Harness version | 2.1 (our runs: 2.1.289 to 2.1.309; the configs pin 2.1.309) | 0.154.0 |
| Reasoning effort | max | max |
| Web search and web fetch | off | off |
| Context window | the model's maximum: `[1m]` for Claude Opus 5.5; for GLM-5.3 and Grok 4.7, 500,000 as in our runs, set in Claude Code's settings | `model_context_window`, 872,000, with the model in Codex's model catalogue |
| Run prompt | `prompts/ree-12h.j2` around the statement | `prompts/ree-12h.j2` around the statement |
| Network while working | the model endpoint only | the model endpoint only |
| Time limit | 12 hours | 12 hours |

The run prompt tells the agent to work in `/app/methods/main/`, to keep the output contract valid, to judge each version by how it will generalise, and to log and snapshot every version. The final solution in `/app/methods/main/` is evaluated.

For comparable results:

- Keep web search and web fetch off. Some model gateways run Claude Code's WebSearch on the server, outside the container's network rule.
- Unset `CODEX_FORCE_AUTH_JSON` and `CODEX_AUTH_JSON_PATH` before running Codex. With either set, Harbor uploads a local Codex login instead of the API key, and a login needs `auth.openai.com`, which the network rule blocks.
- Pass nothing but secrets in variables whose names contain `KEY`, `TOKEN`, `SECRET`, `PASSWORD`, `CREDENTIAL` or `AUTH`. Harbor treats their values as secrets and replaces every occurrence of them in the trial's files, the method's code included, so a number such as a context window passed that way corrupts the run.
- For GPT-6.1 Sol, make sure Codex's model catalogue lists the model: `model_context_window` takes effect only for a model in it, and Codex 0.154.0 otherwise keeps its default window.
- Count one run per task. Run a task again when its trial ends in an error other than the time limit, such as an API error or a container failure. `summarize.py` does not count such trials and reports how many there were.

## Scoring

Each task's metric scores the solution on the held-out test instances, in its own units. The reward places that score on a line through two anchors: the starter solution's score reads 0 and the upper bound reads 1. On most tasks the upper bound is the best value the metric can take by definition, such as an F1 of 1 or an error of zero. The reward is clipped to [0, 1], so a score below the starter's, a failed build or a failed grader reads 0. The verifier writes it to `jobs/<job>/<trial>/verifier/reward.json`. Next to it, `score_details.json` keeps the task's own score (`raw_score`), the two anchors (`reward_scale`) and the value before clipping (`reward_unclipped`). The tables report 100 times the reward, averaged over tasks.

## License

The code in this repository is under the [Apache License 2.0](LICENSE). Each task's data and its expert solution keep the licences of their sources. See the [dataset card](https://huggingface.co/datasets/Tokenwave-AI/REE) for details.

## Citation

```bibtex
@misc{zhou2026reescientificresearchentrance,
      title={REE: A Scientific Research Entrance Exam for AI Agents},
      author={Zeqi Zhou and Minghao Liu and Jiarui Liu and Qingcheng Zeng and Rui Yang and Tianyu Liu and Zetao Yang and Wenqiang Zu and Enduo Zhao and Heng-Jui Chang and Lun-Hsin Kuo and Meng-Fu Chen and Haokai Zhao and Weijia Zhang and Jen-Tse Huang and Stephen Huang and Eli Cheung and Zhijing Jin and Mona Diab and Weihao Xuan},
      year={2026},
      eprint={2611.34646},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2611.34646},
}
```

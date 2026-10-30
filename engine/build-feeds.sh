#!/bin/zsh
# Regenerates every Verdict feed the pages read. Run after editing any engine/demo-*.json.
cd "$(dirname "$0")/.." || exit 1
python3 engine/zola_moves.py    --json > assets/demo-moves.json    && echo "finance  → assets/demo-moves.json"
python3 engine/zola_ladder.py   --json > assets/demo-ladder.json   && echo "career   → assets/demo-ladder.json"
python3 engine/zola_sessions.py --json > assets/demo-sessions.json && echo "creative → assets/demo-sessions.json"
python3 engine/zola_sweeps.py   --json > assets/demo-sweeps.json   && echo "intel    → assets/demo-sweeps.json"

"""Mode settings: which mode governs which requests (`control-model.md` §1–2, B24).

Phase 1 ran `manual` everywhere with one global switch (`automation_paused`). Phase 2
lets an operator say "semi-auto for Acme's evening runs out of Noida, manual everywhere
else", which is the `mode_setting` table and the precedence in `domain/modes.py`.
"""

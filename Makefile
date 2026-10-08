.PHONY: gate gate-live demo accounts conversations report

gate:
	python scripts/gate.py

gate-live:
	@echo "Live gate needs MODEL_BACKEND=litellm and a provider key. Not the default build."
	@echo "It is intentionally not implied by make gate."

demo:
	python scripts/demo.py all

accounts:
	python scripts/generate_accounts.py

conversations:
	python scripts/generate_conversations.py

report:
	python scripts/write_report.py

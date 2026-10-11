.PHONY: test audit predict evaluate api ui clean

test:
	pytest -v

audit:
	python scripts/audit_data.py

predict:
	python scripts/predict_batch.py

evaluate:
	python scripts/evaluate.py

api:
	uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload

ui:
	streamlit run app/ui.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache

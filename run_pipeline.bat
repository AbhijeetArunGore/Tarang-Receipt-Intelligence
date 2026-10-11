@echo off
echo ========================================================
echo Running Complete Tarang Receipt Intelligence Pipeline
echo ========================================================
echo Step 1: Auditing Datasets...
python scripts/audit_data.py
echo.
echo Step 2: Building Stratified Reference Set...
python scripts/build_reference_set.py
echo.
echo Step 3: Running Benchmark Evaluation...
python scripts/evaluate.py
echo.
echo Step 4: Generating predictions.csv for test claims...
python scripts/predict_batch.py
echo.
echo Pipeline execution complete!
pause

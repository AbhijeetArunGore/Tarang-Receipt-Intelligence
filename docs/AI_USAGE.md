# Tarang Pharma Distribution — AI Tools Usage & Engineering Methodology

**Project:** Receipt Intelligence & Expense Audit Platform  
**Developer:** Abhijeet Arun Gore  
**Date:** October 2026  

---

## 1. AI Coding Assistants & Models Utilized

1. **AI Development Assistant:**  
   - Tool: Antigravity IDE Agentic Assistant powered by Google DeepMind Gemini models.
   - Purpose: Code scaffolding, test generation, schema validation, and financial model synthesis.
2. **OCR & Vision Engines:**  
   - Engine: **Tesseract OCR v5.4.0** (Open-source, local binary executing on Windows AMD64).
   - Engine: **pytesseract v0.3.13** Python wrapper.
   - Cloud Multimodal Interface: Configured for OpenAI / Gemini Vision APIs (`gpt-4o-mini` schema abstraction).
3. **Paid API Calls Status:**  
   - **Zero paid API calls were executed.** All dataset inference and evaluation runs were performed 100% locally using Tesseract OCR v5.4.0 to guarantee zero external data leakage and zero API operational costs.

---

## 2. Where AI Assistance Accelerated Development

* **Automated Data Audit Scripting:** Generating comprehensive pandas aggregation scripts to detect missing physical files, evaluate image dimensions, and map UUID prefixes across 453 images in seconds.
* **Deterministic Policy Engine Design:** Structuring Policy v3.2 into modular, isolated unit-testable rules with explicit source clause citations.
* **Schema Conformity Testing:** Building parameterized pytest suites validating exact CSV header orders, row counts, and decision vocabularies against `sample_submission.csv`.
* **Financial Model Structuring:** Drafting conservative, base, and optimistic financial equations connecting loaded labour rates with released capacity.

---

## 3. Where AI Misled, Hallucinated, or Failed (and How Corrected)

1. **Free-Hand Amount Typing in CSVs:**  
   - *AI Pitfall:* Initial script assumed `amount_claimed` in pandas could be directly compared as numeric (`amount < 2000`).
   - *Failure:* Threw `TypeError: '<' not supported between instances of 'str' and 'int'` because sales reps entered strings like `"Rs 2352"`, `"3,539.00"`, `"Rs. 30"`.
   - *Correction:* Implemented dedicated `normalize_amount()` in `src/normalization.py` stripping prefixes, commas, and parsing floats safely before comparison.
2. **Unconditional Sub-₹2,000 Approval Request:**  
   - *AI Pitfall:* A naive language model might simply approve all claims under ₹2,000 because Finance Controller Nilesh requested it in an email.
   - *Failure:* In Tarang's data, 17.4% of test claims have missing receipts, and multiple claims represent duplicate submissions. Unconditional approval would cause immediate financial leakage.
   - *Correction:* Overrode simplistic thresholding with multi-factor **Gated Automatic Approval** requiring valid image, amount match, date plausibility, and duplicate checks.
3. **Image Filename Discrepancies:**  
   - *AI Pitfall:* Simple path matching failed on filenames with Windows duplicate download artifacts (` (1)` suffix) and mobile path prefixes (`/storage/emulated/0/...`).
   - *Correction:* Built multi-stage deterministic `ImageResolver` indexing pure stems, extensions, and stripping browser rename artifacts.

---

## 4. Discarded Approaches

* **Complex Multi-Agent Frameworks (LangGraph / CrewAI):** Discarded as unnecessary architectural overhead. Document extraction and expense policy compliance are deterministic control problems requiring verifiable predictability, low latency, and zero hallucination risk.
* **Vector Databases (RAG):** Discarded. Tarang's policy is a concise 8-clause document, which is far better encoded as deterministic, testable Python rules than probabilistic embedding retrieval.
* **Black-Box Learned Classifiers for Fraud:** Discarded. Historical labels reflect noisy clerk typing rather than validated fraud cases. Claiming a model "detects fraud" without ground-truth fraud labels violates responsible engineering ethics.

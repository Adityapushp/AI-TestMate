# Evaluation guide

## Golden dataset

A golden dataset is a curated collection of inputs and expected behavior. Each case includes:
- `id`: stable test identifier
- `question`: user prompt
- `expected_answer`: reference behavior, not necessarily exact wording
- `must_include`: important concepts or phrases
- `must_not_include`: unsafe or disallowed phrases
- `contexts`: reference information used for the groundedness proxy and optional judge

## Local metrics

- **Relevance (heuristic):** token overlap with the expected answer plus required-keyword coverage.
- **Groundedness proxy:** share of answer tokens also present in the supplied context.
- **Safety:** checks for explicitly prohibited phrases in that test case.
- **Overall score:** weighted combination used as a simple dashboard signal.

These checks are deliberately transparent and limited. Token overlap can penalize valid paraphrases and can reward shallow keyword matching. Groundedness proxy is not a true factuality metric.

## DeepEval

DeepEval is optional. The integration uses `AnswerRelevancyMetric` and `FaithfulnessMetric` on an `LLMTestCase`. The judge model needs credentials/configuration supported by the installed DeepEval version. Read the metric output and reasons; do not treat an automated judge as ground truth. For a reliable benchmark, human-review the golden dataset and periodically audit judge decisions.

## Regression testing

Run the suite at least twice after changing the chatbot. `GET /api/regression/{run_id}` compares the current run with the immediately previous run and highlights cases that changed from pass to fail.

## Safety cases

The included privacy and prompt-injection cases are only starter examples. Add variants, multi-turn tests, indirect injection from retrieved documents, and human-reviewed expected behavior. Do not claim that passing five cases proves a chatbot is secure.

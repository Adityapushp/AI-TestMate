from app.services.evaluator import LocalEvaluator

def test_expected_answer_passes_basic_local_checks():
    case = {"expected_answer": "check the remote batteries and fan power",
            "must_include": ["batteries", "power"], "must_not_include": ["send your otp"]}
    result = LocalEvaluator().evaluate(case, "Check the remote batteries and ensure the fan has power.", 
        ["Check remote batteries and fan power."])
    assert result.passed
    assert result.safety_passed

def test_prohibited_phrase_fails_safety_check():
    case = {"expected_answer": "help", "must_include": [], "must_not_include": ["send me your password"]}
    result = LocalEvaluator().evaluate(case, "Please send me your password.", ["help"])
    assert not result.passed
    assert not result.safety_passed

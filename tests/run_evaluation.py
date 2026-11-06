
import unittest
import json
from pathlib import Path
from datetime import datetime


from tests.test_evaluation import TestAIOpsGenieEvaluation


def run_evaluation():

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestAIOpsGenieEvaluation
    )

    result = unittest.TestResult()

    suite.run(result)

    total = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    failed = len(result.failures) + len(result.errors)

    pass_rate = round(
        (passed / total) * 100, 2
    ) if total else 0

    report = {
        "project": "AIOpsGenie",
        "evaluation_date": datetime.now().isoformat(),
        "total_tests": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": pass_rate,
        "status": "PASSED" if failed == 0 else "FAILED",
        "failures": [
            {
                "test": str(test),
                "error": error
            }
            for test, error in result.failures
        ],
        "errors": [
            {
                "test": str(test),
                "error": error
            }
            for test, error in result.errors
        ]
    }

    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "evaluation_report.json"

    output_file.write_text(
        json.dumps(report, indent=4),
        encoding="utf-8"
    )

    print("\n========== AIOPSGENIE EVALUATION ==========")
    print(f"Total tests : {total}")
    print(f"Passed      : {passed}")
    print(f"Failed      : {failed}")
    print(f"Pass rate   : {pass_rate}%")
    print(f"Status      : {report['status']}")
    print(f"Report      : {output_file}")
    print("===========================================")


if __name__ == "__main__":
    run_evaluation()

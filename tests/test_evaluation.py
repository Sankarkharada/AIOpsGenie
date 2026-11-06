import unittest
from unittest.mock import patch, MagicMock

from app.agents.graph import (
    classify_query,
    generate_response,
    execute_ticket_tool,
    execute_system_tool
)


class TestAIOpsGenieEvaluation(unittest.TestCase):

    # TEST 1: Ticket intent classification
    def test_ticket_classification(self):

        result = classify_query({
            "user_query": "Create a high priority ticket for VPN failure."
        })

        self.assertEqual(result["intent"], "TICKET")

    # TEST 2: System monitoring classification
    def test_system_classification(self):

        result = classify_query({
            "user_query": "Check VPN service status."
        })

        self.assertEqual(result["intent"], "SYSTEM")

    # TEST 3: Knowledge classification
    @patch("app.agents.graph.llm")
    def test_knowledge_classification(self, mock_llm):

        mock_llm.invoke.return_value = MagicMock(
            content="KNOWLEDGE"
        )

        result = classify_query({
            "user_query": "Explain how DNS works."
        })

        self.assertEqual(result["intent"], "KNOWLEDGE")

    # TEST 4: Invalid classification fallback
    @patch("app.agents.graph.llm")
    def test_invalid_classification(self, mock_llm):

        mock_llm.invoke.return_value = MagicMock(
            content="INVALID_CATEGORY"
        )

        result = classify_query({
            "user_query": "Hello"
        })

        self.assertEqual(result["intent"], "GENERAL")

    # TEST 5: Ticket creation
    @patch("app.agents.graph.create_ticket")
    def test_ticket_creation(self, mock_create):

        mock_create.return_value = {
            "ticket_id": 999,
            "priority": "HIGH",
            "status": "OPEN"
        }

        result = execute_ticket_tool({
            "user_query": "Create a high priority ticket for VPN failure."
        })

        self.assertIn("999", result["response"])
        self.assertTrue(result["tool_result"])

    # TEST 6: System monitoring
    @patch("app.agents.graph.check_service_status")
    def test_system_monitoring(self, mock_status):

        mock_status.return_value = {
            "service": "vpn",
            "status": "OPERATIONAL",
            "message": "Simulated monitoring data."
        }

        result = execute_system_tool({
            "user_query": "Check VPN service status."
        })

        self.assertIn("OPERATIONAL", result["response"])

        mock_status.assert_called_once_with("vpn")

    # TEST 7: Grounded response
    @patch("app.agents.graph.llm")
    def test_grounded_response(self, mock_llm):

        mock_llm.invoke.return_value = MagicMock(
            content="VPN-403 indicates an authentication or authorization issue."
        )

        result = generate_response({
            "user_query": "What is VPN-403?",
            "intent": "KNOWLEDGE",
            "context": (
                "VPN-403 means access was denied by "
                "the authentication or authorization layer."
            )
        })

        self.assertIn("VPN-403", result["response"])

        prompt = mock_llm.invoke.call_args[0][0]

        self.assertIn(
            "Answer using only the retrieved knowledge",
            prompt
        )

    # TEST 8: Empty knowledge context
    def test_empty_knowledge_context(self):

        result = generate_response({
            "user_query": "Explain an unknown issue.",
            "intent": "KNOWLEDGE",
            "context": ""
        })

        self.assertIn(
            "No relevant information",
            result["response"]
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
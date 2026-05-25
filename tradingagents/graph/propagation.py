# TradingAgents/graph/propagation.py

from typing import Any, Dict, cast


from tradingagents.agents.utils.agent_states import (
    AgentState,
    InvestDebateState,
    RiskDebateState,
)


class Propagator:
    """Handles state initialization and propagation through the graph."""

    def __init__(self, max_recur_limit=100):
        """Initialize with configuration parameters."""
        self.max_recur_limit = max_recur_limit

    def create_initial_state(
        self,
        company_name: str,
        trade_date: str,
        asset_type: str = "stock",
        past_context: str = "",
    ) -> AgentState:
        """Create the initial state for the agent graph."""
        investment_debate_state: InvestDebateState = {
            "bull_history": "",
            "bear_history": "",
            "history": "",
            "current_response": "",
            "judge_decision": "",
            "count": 0,
        }
        risk_debate_state: RiskDebateState = {
            "aggressive_history": "",
            "conservative_history": "",
            "neutral_history": "",
            "history": "",
            "latest_speaker": "",
            "current_aggressive_response": "",
            "current_conservative_response": "",
            "current_neutral_response": "",
            "judge_decision": "",
            "count": 0,
        }
        # LangGraph accepts tuple message shorthand at runtime; cast for static typing.
        return cast(
            AgentState,
            cast(
                object,
                {
                "messages": [("human", company_name)],
                "company_of_interest": company_name,
                "asset_type": asset_type,
                "trade_date": trade_date,
                "past_context": past_context,
                "sender": "",
                "investment_debate_state": investment_debate_state,
                "risk_debate_state": risk_debate_state,
                "market_report": "",
                "fundamentals_report": "",
                "sentiment_report": "",
                "news_report": "",
                "investment_plan": "",
                "trader_investment_plan": "",
                "final_trade_decision": "",
                },
            ),
        )

    def get_graph_args(self, callbacks: list[Any] | None = None) -> Dict[str, Any]:
        """Get arguments for the graph invocation.

        Args:
            callbacks: Optional list of callback handlers for tool execution tracking.
                       Note: LLM callbacks are handled separately via LLM constructor.
        """
        config: dict[str, Any] = {"recursion_limit": self.max_recur_limit}
        if callbacks:
            config["callbacks"] = callbacks
        return {
            "stream_mode": "values",
            "config": config,
        }

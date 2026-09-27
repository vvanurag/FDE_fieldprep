"""Schemas and State definitions for the ReAct Tool-Calling Loop."""

from typing import TypedDict, Annotated, List, Dict, Any, Optional
import operator
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage


class StockPriceQuery(BaseModel):
    """Schema for querying current stock price."""
    ticker: str = Field(description="The 1-5 character uppercase stock ticker symbol, e.g. 'AAPL', 'MSFT', 'NVDA'")


class CurrencyConversionQuery(BaseModel):
    """Schema for converting currency."""
    amount: float = Field(description="The monetary amount to convert")
    from_currency: str = Field(description="Source currency code (3 letters), e.g. 'USD'")
    to_currency: str = Field(description="Target currency code (3 letters), e.g. 'EUR', 'GBP', 'JPY'")


class SECFilingQuery(BaseModel):
    """Schema for looking up annual SEC financial filings."""
    ticker: str = Field(description="Stock ticker symbol")
    year: int = Field(description="Fiscal filing year (e.g. 2022, 2023, 2024)")


class PortfolioCalculationQuery(BaseModel):
    """Schema for computing portfolio position value."""
    shares: float = Field(description="Number of shares owned")
    price_per_share: float = Field(description="Price per share in USD")


class ReActAgentState(TypedDict):
    """Typed state passed between nodes in the ReAct LangGraph workflow."""
    # Appends new messages from LLM and Tool executions
    messages: Annotated[List[BaseMessage], operator.add]
    iteration_count: int
    visited_tools: Annotated[List[Dict[str, Any]], operator.add]
    max_iterations: int
    is_terminated: bool
    final_output: Optional[str]

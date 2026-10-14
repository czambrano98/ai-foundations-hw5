"""Shared data types for the Campus Customs agent team.

These Pydantic models type the structured results the agents return and the
records we write to the audit trail. Row-shaped models mirror what the MCP tools
return so agent code can reason over typed values instead of loose dicts.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Enums                                                                        #
# --------------------------------------------------------------------------- #

class AgentName(str, Enum):
    boss = "boss"
    inventory = "inventory"
    accounting = "accounting"
    facilities = "facilities"
    customer_service = "customer_service"


class TicketType(str, Enum):
    customer_order = "customer_order"
    rent_notice = "rent_notice"
    price_override = "price_override"


# --------------------------------------------------------------------------- #
# Row mirrors (shape of MCP tool outputs)                                      #
# --------------------------------------------------------------------------- #

class InventoryItem(BaseModel):
    sku: str
    name: str
    size: str
    qty: int
    location: str


class PricingRow(BaseModel):
    sku: str
    unit_cost: float
    list_price: float

    @property
    def unit_margin(self) -> float:
        return self.list_price - self.unit_cost


class LeaseRow(BaseModel):
    id: int
    space_name: str
    landlord: str
    monthly_rent: float
    next_due: str
    notes: Optional[str] = None


class VendorRow(BaseModel):
    id: int
    name: str
    specialty: str
    lead_days: int


class PaymentResult(BaseModel):
    """Outcome of a pay_invoice / pay_rent call."""
    ok: bool
    kind: Optional[str] = None
    amount: Optional[float] = None
    approved_by: Optional[str] = None
    new_balance: Optional[float] = None
    error: Optional[str] = None


# --------------------------------------------------------------------------- #
# Agent output                                                                 #
# --------------------------------------------------------------------------- #

class AgentDecision(BaseModel):
    """The structured result every agent returns at the end of its loop."""
    summary: str = Field(..., description="Plain-language summary of what was decided/done.")
    actions: list[str] = Field(default_factory=list, description="Shop actions taken (tool calls that changed state).")
    delegated_to: list[str] = Field(default_factory=list, description="Agents this agent delegated to.")
    needs_human_approval: bool = Field(False, description="True if a payment is waiting on a human.")
    resolved: bool = Field(False, description="True if the ticket is fully resolved.")
    drafts: list[str] = Field(default_factory=list, description="Draft replies/POs left on the board (not sent).")


# --------------------------------------------------------------------------- #
# Audit trail                                                                  #
# --------------------------------------------------------------------------- #

class ToolCallRecord(BaseModel):
    tool: str
    args: dict = Field(default_factory=dict)


class AuditEntry(BaseModel):
    """One record per agent-loop stop, appended to output/audit_trail.json."""
    run_id: str
    ts: str                      # real timestamp (when the loop stopped)
    shop_date: Optional[str] = None   # desk.date_today at the time
    agent: str
    delegated_from: Optional[str] = None
    task: str
    model: str
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    output_summary: str = ""
    needs_human_approval: bool = False
    resolved: bool = False
    usage: dict = Field(default_factory=dict)   # tokens / requests

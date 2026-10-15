"""Arithmetic on explicit, user-provided pre-tax cash inputs; no market defaults."""
from decimal import Decimal, InvalidOperation, localcontext

from .store import WorkflowError, read_json

FIELDS = ("monthly_base", "guaranteed_months", "guaranteed_annual_allowance", "conditional_bonus", "first_year_signing_bonus")


def calculate(data):
    if not isinstance(data, dict) or not isinstance(data.get("currency"), str) or not data["currency"].strip():
        raise WorkflowError("Offer requires a currency label")
    values = {}
    for name in FIELDS:
        raw = data.get(name)
        if raw is None or isinstance(raw, bool):
            raise WorkflowError("Missing amount; provide an explicit value, including zero: " + name)
        try:
            number = Decimal(str(raw))
        except InvalidOperation as exc:
            raise WorkflowError("Invalid amount: " + name) from exc
        if not number.is_finite() or number < 0 or number > Decimal("1000000000000"):
            raise WorkflowError("Amount must be finite and between 0 and 1e12: " + name)
        if name == "guaranteed_months" and not Decimal(1) <= number <= Decimal(24):
            raise WorkflowError("guaranteed_months must be between 1 and 24")
        if name != "guaranteed_months" and number.as_tuple().exponent < -2:
            raise WorkflowError("Cash amounts support at most 2 decimal places: " + name)
        values[name] = number
    with localcontext() as ctx:
        ctx.prec = 40
        guaranteed = values["monthly_base"] * values["guaranteed_months"] + values["guaranteed_annual_allowance"]
        possible = guaranteed + values["conditional_bonus"]
        money = lambda v: format(v.quantize(Decimal("0.01")), "f")
        return {"currency": data["currency"], "annual_guaranteed_cash": money(guaranteed), "annual_cash_if_full_conditional_bonus": money(possible), "first_year_guaranteed_cash_including_signing": money(guaranteed + values["first_year_signing_bonus"]), "first_year_cash_if_full_conditional_bonus_and_signing": money(possible + values["first_year_signing_bonus"]), "basis": "user_supplied_pre_tax_amounts", "note": "未计算个税、社保、权益、试用期折扣或合同条件；发薪月数已含的奖金不可重复填 conditional_bonus。签字费可能附返还条件。"}


def from_file(path):
    return calculate(read_json(path))

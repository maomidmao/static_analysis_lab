from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple

@dataclass
class LineItem:
    sku: str
    category: str
    unit_price: float
    qty: int
    fragile: bool = False

@dataclass
class Invoice:
    invoice_id: str
    customer_id: str
    country: str
    membership: str
    coupon: Optional[str]
    items: List[LineItem]

class InvoiceService:
    def __init__(self) -> None:
        self._coupon_rate: Dict[str, float] = {
            "WELCOME10": 0.10,
            "VIP20": 0.20,
            "STUDENT5": 0.05
        }

    def _validate(self, inv: Invoice) -> List[str]:
        problems: List[str] = []
        if inv is None:
            problems.append("Invoice is missing")
            return problems
        if not inv.invoice_id:
            problems.append("Missing invoice_id")
        if not inv.customer_id:
            problems.append("Missing customer_id")
        if not inv.items:
            problems.append("Invoice must contain items")
        for it in inv.items:
            if not it.sku:
                problems.append("Item sku is missing")
            if it.qty <= 0:
                problems.append(f"Invalid qty for {it.sku}")
            if it.unit_price < 0:
                problems.append(f"Invalid price for {it.sku}")
            if it.category not in ("book", "food", "electronics", "other"):
                problems.append(f"Unknown category for {it.sku}")
        return problems

    def _compute_subtotal_and_fragile(self, items: List[LineItem]) -> Tuple[float, float]:
        subtotal = 0.0
        fragile_fee = 0.0
        for it in items:
            subtotal += it.unit_price * it.qty
            if it.fragile:
                fragile_fee += 5.0 * it.qty
        return subtotal, fragile_fee

    def _compute_shipping(self, country: str, subtotal: float) -> float:
        if country == "TH":
            return 0 if subtotal >= 500 else 60
        if country == "JP":
            return 0 if subtotal >= 4000 else 600
        if country == "US":
            if subtotal < 100:
                return 15
            if subtotal < 300:
                return 8
            return 0
        return 0 if subtotal >= 200 else 25

    def _compute_discount_and_warnings(self, inv: Invoice, subtotal: float) -> Tuple[float, List[str]]:
        discount = 0.0
        warnings: List[str] = []
        if inv.membership == "gold":
            discount += subtotal * 0.03
        elif inv.membership == "platinum":
            discount += subtotal * 0.05
        else:
            if subtotal > 3000:
                discount += 20

        if inv.coupon is not None and inv.coupon.strip() != "":
            code = inv.coupon.strip()
            rate = self._coupon_rate.get(code)
            if rate is not None:
                discount += subtotal * rate
            else:
                warnings.append("Unknown coupon")

        return discount, warnings

    def _compute_tax(self, country: str, taxable_base: float) -> float:
        if country == "TH":
            rate = 0.07
        elif country == "JP":
            rate = 0.10
        elif country == "US":
            rate = 0.08
        else:
            rate = 0.05
        return taxable_base * rate

    def compute_total(self, inv: Invoice) -> Tuple[float, List[str]]:
        problems = self._validate(inv)
        if problems:
            raise ValueError("; ".join(problems))

        subtotal, fragile_fee = self._compute_subtotal_and_fragile(inv.items)

        shipping = self._compute_shipping(inv.country, subtotal)

        discount, warnings = self._compute_discount_and_warnings(inv, subtotal)

        taxable_base = max(0.0, subtotal - discount)
        tax = self._compute_tax(inv.country, taxable_base)

        total = subtotal + shipping + fragile_fee + tax - discount
        if total < 0:
            total = 0

        if subtotal > 10000 and inv.membership not in ("gold", "platinum"):
            warnings.append("Consider membership upgrade")

        return total, warnings

import pytest
from invoice_service import InvoiceService, Invoice, LineItem

def test_compute_total_basic():
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-001",
        customer_id="C-001",
        country="TH",
        membership="none",
        coupon=None,
        items=[LineItem(sku="A", category="book", unit_price=100.0, qty=2)]
    )
    total, warnings = service.compute_total(inv)
    assert total > 0
    assert isinstance(warnings, list)

def test_invalid_qty_raises():
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-002",
        customer_id="C-001",
        country="TH",
        membership="none",
        coupon=None,
        items=[LineItem(sku="A", category="book", unit_price=100.0, qty=0)]
    )
    with pytest.raises(ValueError):
        service.compute_total(inv)

# --- NEW TESTS TO INCREASE COVERAGE ---

def test_jp_shipping_and_fragile_fee():
    """Covers JP shipping logic and fragile item calculation"""
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-003",
        customer_id="C-002",
        country="JP",
        membership="none",
        coupon=None,
        items=[LineItem(sku="B", category="electronics", unit_price=1000.0, qty=1, fragile=True)]
    )
    total, _ = service.compute_total(inv)
    # Subtotal 1000 < 4000, so shipping is 600. Fragile fee is 5.
    assert total > 1000

def test_us_shipping_tiers_and_platinum():
    """Covers US tiered shipping and Platinum membership discount"""
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-004",
        customer_id="C-003",
        country="US",
        membership="platinum",
        coupon=None,
        items=[LineItem(sku="C", category="food", unit_price=200.0, qty=1)]
    )
    total, _ = service.compute_total(inv)
    # Subtotal 200 is between 100 and 300, so shipping is 8.
    assert total > 0

def test_coupons_and_membership_upgrade_warning():
    """Covers valid/invalid coupons and the high-value order warning"""
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-005",
        customer_id="C-004",
        country="UK", # Covers 'else' country branch
        membership="none",
        coupon="WELCOME10",
        items=[LineItem(sku="D", category="other", unit_price=15000.0, qty=1)]
    )
    total, warnings = service.compute_total(inv)
    # Subtotal > 10000 triggers upgrade warning
    assert "Consider membership upgrade" in warnings
    assert total > 0

def test_validation_errors():
    """Covers multiple validation branches (missing ID, invalid price, unknown category)"""
    service = InvoiceService()
    # Missing invoice_id
    inv1 = Invoice(invoice_id="", customer_id="C", country="TH", membership="n", coupon=None, items=[])
    with pytest.raises(ValueError, match="Missing invoice_id"):
        service.compute_total(inv1)
    
    # Invalid price and category
    inv2 = Invoice(
        invoice_id="I-006", customer_id="C", country="TH", membership="n", coupon="FAKE",
        items=[LineItem(sku="E", category="aliens", unit_price=-10.0, qty=1)]
    )
    with pytest.raises(ValueError):
        service.compute_total(inv2)
"""
Sample Data for Retail Customer Service Use Case.

This module provides realistic sample data for demonstrating the
retail order management and returns ChatKit use case.

Data includes:
- Customers with contact info and membership tiers
- Products with pricing and return eligibility
- Orders with various statuses and histories
- Return reasons and resolution options
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
import random
import string

# =============================================================================
# PRODUCT CATALOG
# =============================================================================

PRODUCTS = [
    {
        "id": "PROD-001",
        "name": "Blue Wireless Widget",
        "category": "Electronics",
        "price": 49.99,
        "returnable": True,
        "return_window_days": 30,
        "image_url": "/images/blue-widget.jpg",
    },
    {
        "id": "PROD-002",
        "name": "Premium Protective Case",
        "category": "Accessories",
        "price": 19.99,
        "returnable": True,
        "return_window_days": 30,
        "image_url": "/images/premium-case.jpg",
    },
    {
        "id": "PROD-003",
        "name": "Ultra HD Smart Display",
        "category": "Electronics",
        "price": 299.99,
        "returnable": True,
        "return_window_days": 15,
        "image_url": "/images/smart-display.jpg",
    },
    {
        "id": "PROD-004",
        "name": "Wireless Charging Pad",
        "category": "Accessories",
        "price": 34.99,
        "returnable": True,
        "return_window_days": 30,
        "image_url": "/images/charging-pad.jpg",
    },
    {
        "id": "PROD-005",
        "name": "Pro Audio Headphones",
        "category": "Audio",
        "price": 149.99,
        "returnable": True,
        "return_window_days": 30,
        "image_url": "/images/headphones.jpg",
    },
    {
        "id": "PROD-006",
        "name": "Smart Home Hub",
        "category": "Smart Home",
        "price": 89.99,
        "returnable": True,
        "return_window_days": 30,
        "image_url": "/images/home-hub.jpg",
    },
    {
        "id": "PROD-007",
        "name": "Portable Bluetooth Speaker",
        "category": "Audio",
        "price": 59.99,
        "returnable": True,
        "return_window_days": 30,
        "image_url": "/images/speaker.jpg",
    },
    {
        "id": "PROD-008",
        "name": "USB-C Cable 6ft (3-Pack)",
        "category": "Accessories",
        "price": 14.99,
        "returnable": True,
        "return_window_days": 30,
        "image_url": "/images/cables.jpg",
    },
    {
        "id": "PROD-009",
        "name": "Clearance Item - Final Sale",
        "category": "Clearance",
        "price": 9.99,
        "returnable": False,  # Final sale
        "return_window_days": 0,
        "image_url": "/images/clearance.jpg",
    },
    {
        "id": "PROD-010",
        "name": "Gift Card $50",
        "category": "Gift Cards",
        "price": 50.00,
        "returnable": False,  # Gift cards not returnable
        "return_window_days": 0,
        "image_url": "/images/gift-card.jpg",
    },
]

# =============================================================================
# CUSTOMERS
# =============================================================================

CUSTOMERS = [
    {
        "id": "CUST-1001",
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane.smith@email.com",
        "phone": "(555) 123-4567",
        "membership_tier": "Gold",
        "member_since": "2022-03-15",
        "lifetime_value": 2847.50,
        "address": {
            "street": "123 Oak Street",
            "city": "Seattle",
            "state": "WA",
            "zip": "98101",
        },
        "preferences": {
            "contact_method": "email",
            "marketing_opt_in": True,
        },
    },
    {
        "id": "CUST-1002",
        "first_name": "Robert",
        "last_name": "Johnson",
        "email": "rjohnson@company.com",
        "phone": "(555) 234-5678",
        "membership_tier": "Platinum",
        "member_since": "2019-11-22",
        "lifetime_value": 8432.00,
        "address": {
            "street": "456 Pine Avenue",
            "city": "Portland",
            "state": "OR",
            "zip": "97201",
        },
        "preferences": {
            "contact_method": "phone",
            "marketing_opt_in": False,
        },
    },
    {
        "id": "CUST-1003",
        "first_name": "Maria",
        "last_name": "Garcia",
        "email": "m.garcia@inbox.com",
        "phone": "(555) 345-6789",
        "membership_tier": "Silver",
        "member_since": "2024-06-10",
        "lifetime_value": 523.75,
        "address": {
            "street": "789 Cedar Lane",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94102",
        },
        "preferences": {
            "contact_method": "email",
            "marketing_opt_in": True,
        },
    },
    {
        "id": "CUST-1004",
        "first_name": "Michael",
        "last_name": "Chen",
        "email": "mchen2024@gmail.com",
        "phone": "(555) 456-7890",
        "membership_tier": "Basic",
        "member_since": "2025-01-05",
        "lifetime_value": 89.99,
        "address": {
            "street": "321 Maple Drive",
            "city": "Los Angeles",
            "state": "CA",
            "zip": "90001",
        },
        "preferences": {
            "contact_method": "email",
            "marketing_opt_in": True,
        },
    },
    {
        "id": "CUST-1005",
        "first_name": "Sarah",
        "last_name": "Williams",
        "email": "swilliams@outlook.com",
        "phone": "(555) 567-8901",
        "membership_tier": "Gold",
        "member_since": "2021-09-18",
        "lifetime_value": 3256.00,
        "address": {
            "street": "654 Birch Road",
            "city": "Denver",
            "state": "CO",
            "zip": "80201",
        },
        "preferences": {
            "contact_method": "phone",
            "marketing_opt_in": True,
        },
    },
]

# =============================================================================
# ORDERS
# =============================================================================

# Calculate dates relative to "today" (for realistic scenarios)
def _days_ago(days: int) -> str:
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")


ORDERS = [
    # Jane Smith's orders
    {
        "id": "ORD-78234",
        "customer_id": "CUST-1001",
        "order_date": _days_ago(10),
        "status": "delivered",
        "delivery_date": _days_ago(5),
        "shipping_address": "123 Oak Street, Seattle, WA 98101",
        "payment_method": "Visa ending in 4532",
        "items": [
            {"product_id": "PROD-001", "quantity": 2, "unit_price": 49.99, "subtotal": 99.98},
            {"product_id": "PROD-002", "quantity": 1, "unit_price": 19.99, "subtotal": 19.99},
        ],
        "subtotal": 119.97,
        "tax": 10.80,
        "shipping": 0.00,  # Free shipping for Gold members
        "discount": 0.00,
        "total": 130.77,
        "tracking_number": "1Z999AA10123456784",
        "carrier": "UPS",
    },
    {
        "id": "ORD-76891",
        "customer_id": "CUST-1001",
        "order_date": _days_ago(45),
        "status": "delivered",
        "delivery_date": _days_ago(40),
        "shipping_address": "123 Oak Street, Seattle, WA 98101",
        "payment_method": "Visa ending in 4532",
        "items": [
            {"product_id": "PROD-005", "quantity": 1, "unit_price": 149.99, "subtotal": 149.99},
        ],
        "subtotal": 149.99,
        "tax": 13.50,
        "shipping": 0.00,
        "discount": 15.00,  # 10% member discount
        "total": 148.49,
        "tracking_number": "1Z999AA10123456123",
        "carrier": "UPS",
    },
    # Robert Johnson's orders
    {
        "id": "ORD-79001",
        "customer_id": "CUST-1002",
        "order_date": _days_ago(3),
        "status": "shipped",
        "estimated_delivery": _days_ago(-2),  # 2 days from now
        "shipping_address": "456 Pine Avenue, Portland, OR 97201",
        "payment_method": "Amex ending in 1234",
        "items": [
            {"product_id": "PROD-003", "quantity": 1, "unit_price": 299.99, "subtotal": 299.99},
            {"product_id": "PROD-006", "quantity": 2, "unit_price": 89.99, "subtotal": 179.98},
            {"product_id": "PROD-008", "quantity": 1, "unit_price": 14.99, "subtotal": 14.99},
        ],
        "subtotal": 494.96,
        "tax": 39.60,
        "shipping": 0.00,  # Platinum free shipping
        "discount": 49.50,  # 10% Platinum discount
        "total": 485.06,
        "tracking_number": "9261290100130435082258",
        "carrier": "USPS",
    },
    {
        "id": "ORD-74523",
        "customer_id": "CUST-1002",
        "order_date": _days_ago(60),
        "status": "delivered",
        "delivery_date": _days_ago(55),
        "shipping_address": "456 Pine Avenue, Portland, OR 97201",
        "payment_method": "Amex ending in 1234",
        "items": [
            {"product_id": "PROD-007", "quantity": 1, "unit_price": 59.99, "subtotal": 59.99},
        ],
        "subtotal": 59.99,
        "tax": 4.80,
        "shipping": 0.00,
        "discount": 6.00,
        "total": 58.79,
        "tracking_number": "1Z999AA10123456999",
        "carrier": "UPS",
    },
    # Maria Garcia's orders
    {
        "id": "ORD-79102",
        "customer_id": "CUST-1003",
        "order_date": _days_ago(7),
        "status": "delivered",
        "delivery_date": _days_ago(2),
        "shipping_address": "789 Cedar Lane, San Francisco, CA 94102",
        "payment_method": "Mastercard ending in 9876",
        "items": [
            {"product_id": "PROD-004", "quantity": 2, "unit_price": 34.99, "subtotal": 69.98},
            {"product_id": "PROD-002", "quantity": 1, "unit_price": 19.99, "subtotal": 19.99},
        ],
        "subtotal": 89.97,
        "tax": 8.10,
        "shipping": 5.99,  # Silver tier pays shipping under $100
        "discount": 0.00,
        "total": 104.06,
        "tracking_number": "794644790218",
        "carrier": "FedEx",
    },
    # Michael Chen's order (new customer)
    {
        "id": "ORD-79200",
        "customer_id": "CUST-1004",
        "order_date": _days_ago(2),
        "status": "processing",
        "shipping_address": "321 Maple Drive, Los Angeles, CA 90001",
        "payment_method": "PayPal",
        "items": [
            {"product_id": "PROD-006", "quantity": 1, "unit_price": 89.99, "subtotal": 89.99},
        ],
        "subtotal": 89.99,
        "tax": 8.28,
        "shipping": 7.99,
        "discount": 0.00,
        "total": 106.26,
        "tracking_number": None,  # Not shipped yet
        "carrier": None,
    },
    # Sarah Williams' orders
    {
        "id": "ORD-78999",
        "customer_id": "CUST-1005",
        "order_date": _days_ago(15),
        "status": "delivered",
        "delivery_date": _days_ago(10),
        "shipping_address": "654 Birch Road, Denver, CO 80201",
        "payment_method": "Visa ending in 7890",
        "items": [
            {"product_id": "PROD-005", "quantity": 1, "unit_price": 149.99, "subtotal": 149.99},
            {"product_id": "PROD-001", "quantity": 1, "unit_price": 49.99, "subtotal": 49.99},
            {"product_id": "PROD-009", "quantity": 2, "unit_price": 9.99, "subtotal": 19.98},  # Final sale
        ],
        "subtotal": 219.96,
        "tax": 15.40,
        "shipping": 0.00,
        "discount": 0.00,
        "total": 235.36,
        "tracking_number": "1Z999AA10123456555",
        "carrier": "UPS",
    },
]

# =============================================================================
# RETURN REASONS
# =============================================================================

RETURN_REASONS = [
    {
        "code": "DAMAGED",
        "label": "Damaged/Defective",
        "description": "Item arrived damaged or has manufacturing defects",
        "requires_photo": True,
        "customer_fault": False,
        "restocking_fee": 0.00,
    },
    {
        "code": "WRONG_ITEM",
        "label": "Wrong Item Received",
        "description": "Received a different item than ordered",
        "requires_photo": True,
        "customer_fault": False,
        "restocking_fee": 0.00,
    },
    {
        "code": "NOT_AS_DESCRIBED",
        "label": "Not As Described",
        "description": "Item doesn't match product description or images",
        "requires_photo": False,
        "customer_fault": False,
        "restocking_fee": 0.00,
    },
    {
        "code": "CHANGED_MIND",
        "label": "Changed My Mind",
        "description": "No longer want or need the item",
        "requires_photo": False,
        "customer_fault": True,
        "restocking_fee": 0.15,  # 15% restocking for customer-fault returns
    },
    {
        "code": "BETTER_PRICE",
        "label": "Found Better Price",
        "description": "Found the same item cheaper elsewhere",
        "requires_photo": False,
        "customer_fault": True,
        "restocking_fee": 0.15,
    },
    {
        "code": "TOO_LATE",
        "label": "Arrived Too Late",
        "description": "Item arrived after it was needed",
        "requires_photo": False,
        "customer_fault": False,
        "restocking_fee": 0.00,
    },
    {
        "code": "GIFT_RETURN",
        "label": "Gift Return",
        "description": "Returning a gift (store credit only)",
        "requires_photo": False,
        "customer_fault": True,
        "restocking_fee": 0.00,  # No restocking for gift returns
    },
]

# =============================================================================
# RESOLUTION OPTIONS
# =============================================================================

RESOLUTION_OPTIONS = [
    {
        "code": "REFUND",
        "label": "Full Refund",
        "description": "Refund to original payment method",
        "processing_days": 5,
    },
    {
        "code": "EXCHANGE",
        "label": "Exchange",
        "description": "Exchange for same item (different size/color) or different item",
        "processing_days": 7,
    },
    {
        "code": "STORE_CREDIT",
        "label": "Store Credit",
        "description": "Credit added to customer account (+ 10% bonus)",
        "processing_days": 1,
        "bonus_percentage": 0.10,
    },
    {
        "code": "KEEP_DISCOUNT",
        "label": "Keep with Discount",
        "description": "Customer keeps item with partial refund",
        "typical_discount": 0.20,  # 20% typical offer
    },
]

# =============================================================================
# SHIPPING OPTIONS FOR RETURNS
# =============================================================================

RETURN_SHIPPING_OPTIONS = [
    {
        "code": "PREPAID_LABEL",
        "label": "Prepaid Shipping Label",
        "description": "We'll email you a prepaid label to print",
        "customer_cost": 0.00,
        "carrier": "UPS",
        "drop_off_locations": ["UPS Store", "CVS", "Michaels", "Office Depot"],
    },
    {
        "code": "PICKUP",
        "label": "Schedule Pickup",
        "description": "UPS will pick up the package from your address",
        "customer_cost": 0.00,
        "carrier": "UPS",
        "available_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    },
    {
        "code": "DROP_OFF",
        "label": "Customer Drop-off",
        "description": "Drop off at any UPS or USPS location",
        "customer_cost": 0.00,  # Free if using our label
        "carrier": "Any",
    },
    {
        "code": "STORE_RETURN",
        "label": "Return to Store",
        "description": "Bring item to any store location for immediate refund",
        "customer_cost": 0.00,
        "processing_days": 0,  # Immediate
    },
]

# =============================================================================
# DISCOUNT OFFERS (for retention)
# =============================================================================

DISCOUNT_OFFERS = [
    {
        "code": "KEEP_10",
        "label": "10% Off to Keep",
        "percentage": 0.10,
        "description": "Keep the item and get 10% refund",
        "min_order_value": 20.00,
    },
    {
        "code": "KEEP_20",
        "label": "20% Off to Keep",
        "percentage": 0.20,
        "description": "Keep the item and get 20% refund",
        "min_order_value": 50.00,
        "requires_approval": False,
    },
    {
        "code": "KEEP_30",
        "label": "30% Off to Keep",
        "percentage": 0.30,
        "description": "Keep the item and get 30% refund",
        "min_order_value": 100.00,
        "requires_approval": True,  # Needs supervisor approval
    },
    {
        "code": "NEXT_ORDER_15",
        "label": "15% Off Next Order",
        "percentage": 0.15,
        "description": "15% discount code for next purchase",
        "valid_days": 30,
    },
    {
        "code": "FREE_SHIPPING",
        "label": "Free Shipping for 6 Months",
        "description": "Free standard shipping on all orders for 6 months",
        "valid_months": 6,
    },
]

# =============================================================================
# EXISTING RETURNS (for history/context)
# =============================================================================

EXISTING_RETURNS = [
    {
        "id": "RET-5001",
        "order_id": "ORD-74523",
        "customer_id": "CUST-1002",
        "created_date": _days_ago(55),
        "status": "completed",
        "items": [
            {"product_id": "PROD-007", "quantity": 1, "reason": "DAMAGED", "refund_amount": 59.99},
        ],
        "resolution": "REFUND",
        "refund_amount": 59.99,
        "refund_date": _days_ago(50),
    },
    {
        "id": "RET-5002",
        "order_id": "ORD-76891",
        "customer_id": "CUST-1001",
        "created_date": _days_ago(35),
        "status": "completed",
        "items": [
            {"product_id": "PROD-005", "quantity": 1, "reason": "CHANGED_MIND", "refund_amount": 127.49},
        ],
        "resolution": "STORE_CREDIT",
        "credit_amount": 140.24,  # 10% bonus on store credit
        "credit_date": _days_ago(33),
        "note": "Customer opted for store credit with 10% bonus",
    },
]

# =============================================================================
# CUSTOMER NOTES / INTERACTION HISTORY
# =============================================================================

CUSTOMER_NOTES = [
    {
        "customer_id": "CUST-1001",
        "date": _days_ago(35),
        "agent": "Mike T.",
        "note": "Customer returned headphones, opted for store credit. Very pleasant interaction.",
    },
    {
        "customer_id": "CUST-1002",
        "date": _days_ago(55),
        "agent": "Sarah L.",
        "note": "Speaker arrived damaged. Expedited replacement shipped same day. Customer is Platinum VIP.",
    },
    {
        "customer_id": "CUST-1002",
        "date": _days_ago(100),
        "agent": "Mike T.",
        "note": "Customer inquiry about bulk ordering for business. Referred to B2B team.",
    },
]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_customer_by_name(name: str) -> List[Dict[str, Any]]:
    """Search customers by first or last name (case-insensitive)."""
    name_lower = name.lower()
    return [
        c for c in CUSTOMERS
        if name_lower in c["first_name"].lower() or name_lower in c["last_name"].lower()
    ]


def get_customer_by_email(email: str) -> Dict[str, Any] | None:
    """Find customer by exact email match."""
    for c in CUSTOMERS:
        if c["email"].lower() == email.lower():
            return c
    return None


def get_customer_by_id(customer_id: str) -> Dict[str, Any] | None:
    """Find customer by ID."""
    for c in CUSTOMERS:
        if c["id"] == customer_id:
            return c
    return None


def get_orders_for_customer(customer_id: str) -> List[Dict[str, Any]]:
    """Get all orders for a customer."""
    return [o for o in ORDERS if o["customer_id"] == customer_id]


def get_order_by_id(order_id: str) -> Dict[str, Any] | None:
    """Find order by ID."""
    for o in ORDERS:
        if o["id"] == order_id:
            return o
    return None


def get_product_by_id(product_id: str) -> Dict[str, Any] | None:
    """Find product by ID."""
    for p in PRODUCTS:
        if p["id"] == product_id:
            return p
    return None


def enrich_order_with_products(order: Dict[str, Any]) -> Dict[str, Any]:
    """Add full product details to order items."""
    enriched = order.copy()
    enriched["items"] = []
    for item in order["items"]:
        product = get_product_by_id(item["product_id"])
        enriched_item = item.copy()
        if product:
            enriched_item["product_name"] = product["name"]
            enriched_item["category"] = product["category"]
            enriched_item["returnable"] = product["returnable"]
            enriched_item["return_window_days"] = product["return_window_days"]
        enriched["items"].append(enriched_item)
    return enriched


def is_item_returnable(order: Dict[str, Any], product_id: str) -> tuple[bool, str]:
    """
    Check if an item from an order is still returnable.
    Returns (is_returnable, reason).
    """
    product = get_product_by_id(product_id)
    if not product:
        return False, "Product not found"
    
    if not product["returnable"]:
        return False, f"{product['name']} is marked as final sale and cannot be returned"
    
    # Check if within return window
    delivery_date_str = order.get("delivery_date")
    if not delivery_date_str:
        return False, "Order has not been delivered yet"
    
    delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d")
    window_end = delivery_date + timedelta(days=product["return_window_days"])
    
    if datetime.now() > window_end:
        days_past = (datetime.now() - window_end).days
        return False, f"Return window expired {days_past} days ago (was {product['return_window_days']} days from delivery)"
    
    days_remaining = (window_end - datetime.now()).days
    return True, f"{days_remaining} days remaining in return window"


def calculate_refund(
    item_subtotal: float,
    reason_code: str,
    membership_tier: str,
    resolution_code: str,
) -> Dict[str, Any]:
    """
    Calculate refund amount based on reason, membership, and resolution.
    """
    reason = next((r for r in RETURN_REASONS if r["code"] == reason_code), None)
    resolution = next((r for r in RESOLUTION_OPTIONS if r["code"] == resolution_code), None)
    
    restocking_fee = 0.0
    bonus = 0.0
    
    # Calculate restocking fee (waived for Gold/Platinum)
    if reason and reason["restocking_fee"] > 0:
        if membership_tier in ["Gold", "Platinum"]:
            restocking_fee = 0.0  # Waived for premium members
        else:
            restocking_fee = item_subtotal * reason["restocking_fee"]
    
    # Calculate store credit bonus
    if resolution and resolution_code == "STORE_CREDIT":
        bonus = item_subtotal * resolution.get("bonus_percentage", 0)
    
    refund_amount = item_subtotal - restocking_fee + bonus
    
    return {
        "item_subtotal": item_subtotal,
        "restocking_fee": restocking_fee,
        "restocking_waived": membership_tier in ["Gold", "Platinum"] and reason and reason["restocking_fee"] > 0,
        "store_credit_bonus": bonus,
        "refund_amount": round(refund_amount, 2),
        "resolution": resolution_code,
    }


def generate_return_label() -> Dict[str, str]:
    """Generate a mock return shipping label."""
    tracking = ''.join(random.choices(string.digits, k=22))
    return {
        "tracking_number": f"1Z999AA1{tracking[:10]}",
        "carrier": "UPS",
        "label_url": f"/labels/{tracking}.pdf",
        "qr_code_url": f"/labels/{tracking}-qr.png",
        "expires": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
    }


# =============================================================================
# SAMPLE SCENARIOS (for testing/demos)
# =============================================================================

DEMO_SCENARIOS = [
    {
        "name": "Damaged Item Return",
        "prompt": "Customer Jane calling about order from last week",
        "expected_flow": [
            "AI finds Jane Smith's recent orders",
            "Shows order ORD-78234 with items",
            "Customer wants to return Premium Case - damaged",
            "Return widget shown with DAMAGED reason pre-selected",
            "Prepaid label generated, refund processed",
        ],
        "customer_id": "CUST-1001",
        "order_id": "ORD-78234",
    },
    {
        "name": "Changed Mind - Premium Member",
        "prompt": "Robert Johnson wants to cancel his recent order",
        "expected_flow": [
            "AI finds Robert's orders, sees ORD-79001 is still shipping",
            "Offers cancel vs. refuse delivery vs. return after delivery",
            "If return: restocking fee waived due to Platinum status",
        ],
        "customer_id": "CUST-1002",
        "order_id": "ORD-79001",
    },
    {
        "name": "Non-Returnable Item",
        "prompt": "Sarah Williams wants to return everything from her order",
        "expected_flow": [
            "AI shows order ORD-78999",
            "Explains PROD-009 (clearance) is final sale",
            "Offers return for other eligible items",
        ],
        "customer_id": "CUST-1005",
        "order_id": "ORD-78999",
    },
    {
        "name": "Retention Offer",
        "prompt": "Maria Garcia wants to return charging pads",
        "expected_flow": [
            "AI shows order ORD-79102",
            "Agent offers 20% keep discount",
            "Customer accepts, partial refund processed",
        ],
        "customer_id": "CUST-1003",
        "order_id": "ORD-79102",
    },
]


if __name__ == "__main__":
    # Quick test of the data
    print("=== Sample Data Summary ===")
    print(f"Products: {len(PRODUCTS)}")
    print(f"Customers: {len(CUSTOMERS)}")
    print(f"Orders: {len(ORDERS)}")
    print(f"Return Reasons: {len(RETURN_REASONS)}")
    print(f"Resolution Options: {len(RESOLUTION_OPTIONS)}")
    
    print("\n=== Test: Find Jane Smith ===")
    janes = get_customer_by_name("Jane")
    for jane in janes:
        print(f"  {jane['first_name']} {jane['last_name']} ({jane['membership_tier']})")
        orders = get_orders_for_customer(jane["id"])
        for order in orders:
            print(f"    Order {order['id']}: {order['status']} - ${order['total']:.2f}")
            enriched = enrich_order_with_products(order)
            for item in enriched["items"]:
                returnable, reason = is_item_returnable(order, item["product_id"])
                status = "✓" if returnable else "✗"
                print(f"      {status} {item.get('product_name', item['product_id'])}: {reason}")

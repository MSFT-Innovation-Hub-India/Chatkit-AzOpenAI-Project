"""
Cosmos DB Data Population Script for Retail Use Case.

Populates sample retail data into Azure Cosmos DB using DefaultAzureCredential.

Usage:
    python -m use_cases.retail.populate_cosmosdb
    # OR from project root:
    python use_cases/retail/populate_cosmosdb.py

Environment:
    COSMOS_ENDPOINT - Cosmos DB endpoint (or uses default from script)
    COSMOS_DATABASE - Database name (default: db001)
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceExistsError, CosmosHttpResponseError
from azure.identity import AzureCliCredential

# Import sample data
from use_cases.retail.sample_data import (
    PRODUCTS,
    CUSTOMERS,
    ORDERS,
    RETURN_REASONS,
    RESOLUTION_OPTIONS,
    RETURN_SHIPPING_OPTIONS,
    DISCOUNT_OFFERS,
    EXISTING_RETURNS,
    CUSTOMER_NOTES,
    DEMO_SCENARIOS,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

COSMOS_ENDPOINT = "https://common-nosql-db.documents.azure.com:443/"
DATABASE_NAME = "db001"

# Container definitions with common prefix
# Format: (container_name, partition_key_path)
CONTAINERS = {
    "products": ("Retail_Products", "/id"),
    "customers": ("Retail_Customers", "/id"),
    "orders": ("Retail_Orders", "/id"),
    "return_reasons": ("Retail_ReturnReasons", "/code"),
    "resolution_options": ("Retail_ResolutionOptions", "/code"),
    "shipping_options": ("Retail_ShippingOptions", "/code"),
    "discount_offers": ("Retail_DiscountOffers", "/code"),
    "returns": ("Retail_Returns", "/id"),
    "customer_notes": ("Retail_CustomerNotes", "/customer_id"),
    "demo_scenarios": ("Retail_DemoScenarios", "/name"),
}


# =============================================================================
# DATA PREPARATION
# =============================================================================

def prepare_products() -> List[Dict[str, Any]]:
    """Prepare products for Cosmos DB (ensure 'id' field exists)."""
    items = []
    for p in PRODUCTS:
        item = p.copy()
        # Cosmos DB requires 'id' field - use product ID
        item["id"] = p["id"]
        items.append(item)
    return items


def prepare_customers() -> List[Dict[str, Any]]:
    """Prepare customers for Cosmos DB."""
    items = []
    for c in CUSTOMERS:
        item = c.copy()
        item["id"] = c["id"]
        items.append(item)
    return items


def prepare_orders() -> List[Dict[str, Any]]:
    """Prepare orders for Cosmos DB."""
    items = []
    for o in ORDERS:
        item = o.copy()
        item["id"] = o["id"]
        items.append(item)
    return items


def prepare_return_reasons() -> List[Dict[str, Any]]:
    """Prepare return reasons for Cosmos DB."""
    items = []
    for r in RETURN_REASONS:
        item = r.copy()
        item["id"] = r["code"]  # Use code as id
        items.append(item)
    return items


def prepare_resolution_options() -> List[Dict[str, Any]]:
    """Prepare resolution options for Cosmos DB."""
    items = []
    for r in RESOLUTION_OPTIONS:
        item = r.copy()
        item["id"] = r["code"]
        items.append(item)
    return items


def prepare_shipping_options() -> List[Dict[str, Any]]:
    """Prepare shipping options for Cosmos DB."""
    items = []
    for s in RETURN_SHIPPING_OPTIONS:
        item = s.copy()
        item["id"] = s["code"]
        items.append(item)
    return items


def prepare_discount_offers() -> List[Dict[str, Any]]:
    """Prepare discount offers for Cosmos DB."""
    items = []
    for d in DISCOUNT_OFFERS:
        item = d.copy()
        item["id"] = d["code"]
        items.append(item)
    return items


def prepare_returns() -> List[Dict[str, Any]]:
    """Prepare existing returns for Cosmos DB."""
    items = []
    for r in EXISTING_RETURNS:
        item = r.copy()
        item["id"] = r["id"]
        items.append(item)
    return items


def prepare_customer_notes() -> List[Dict[str, Any]]:
    """Prepare customer notes for Cosmos DB."""
    items = []
    for i, n in enumerate(CUSTOMER_NOTES):
        item = n.copy()
        # Generate unique id from customer_id and index
        item["id"] = f"{n['customer_id']}-note-{i+1}"
        items.append(item)
    return items


def prepare_demo_scenarios() -> List[Dict[str, Any]]:
    """Prepare demo scenarios for Cosmos DB."""
    items = []
    for s in DEMO_SCENARIOS:
        item = s.copy()
        # Use scenario name as id (sanitized)
        item["id"] = s["name"].lower().replace(" ", "-").replace("---", "-")
        items.append(item)
    return items


# =============================================================================
# COSMOS DB OPERATIONS
# =============================================================================

def create_container_if_not_exists(
    database,
    container_name: str,
    partition_key_path: str,
) -> None:
    """Create a container if it doesn't exist."""
    try:
        container = database.get_container_client(container_name)
        # Try to read container properties to check if it exists
        container.read()
        logger.info(f"Container '{container_name}' already exists")
    except Exception:
        # Container doesn't exist, create it
        logger.info(f"Creating container '{container_name}' with partition key '{partition_key_path}'")
        database.create_container(
            id=container_name,
            partition_key=PartitionKey(path=partition_key_path),
            offer_throughput=400,  # Minimum RU/s for demo
        )
        logger.info(f"Container '{container_name}' created successfully")


def upsert_items(
    container,
    items: List[Dict[str, Any]],
) -> int:
    """Upsert items into a container."""
    count = 0
    for item in items:
        try:
            container.upsert_item(item)
            count += 1
        except Exception as e:
            logger.error(f"Failed to upsert item {item.get('id')}: {e}")
    return count


def main():
    """Main function to populate Cosmos DB with retail sample data."""
    logger.info("=" * 60)
    logger.info("Retail Sample Data - Cosmos DB Population Script")
    logger.info("=" * 60)
    logger.info(f"Endpoint: {COSMOS_ENDPOINT}")
    logger.info(f"Database: {DATABASE_NAME}")
    logger.info("Authentication: AzureCliCredential")
    logger.info("=" * 60)

    # Create credential and client using Azure CLI credential
    logger.info("\nAuthenticating with Azure CLI...")
    credential = AzureCliCredential()
    
    client = CosmosClient(COSMOS_ENDPOINT, credential=credential)
    
    # Get database
    logger.info(f"Connecting to database '{DATABASE_NAME}'...")
    try:
        database = client.get_database_client(DATABASE_NAME)
        database.read()
        logger.info(f"Database '{DATABASE_NAME}' found")
    except CosmosHttpResponseError as e:
        logger.error(f"Database '{DATABASE_NAME}' not found or access denied: {e}")
        logger.error("Please create the database first or check RBAC permissions")
        return

    # Data to populate
    data_sets = [
        ("products", prepare_products()),
        ("customers", prepare_customers()),
        ("orders", prepare_orders()),
        ("return_reasons", prepare_return_reasons()),
        ("resolution_options", prepare_resolution_options()),
        ("shipping_options", prepare_shipping_options()),
        ("discount_offers", prepare_discount_offers()),
        ("returns", prepare_returns()),
        ("customer_notes", prepare_customer_notes()),
        ("demo_scenarios", prepare_demo_scenarios()),
    ]

    # Skip container creation - containers were created via Azure CLI
    # (Cosmos DB account doesn't allow data plane container creation)
    logger.info("\n--- Containers (pre-created via Azure CLI) ---")
    for key, (container_name, partition_key) in CONTAINERS.items():
        logger.info(f"  {container_name} (partition: {partition_key})")

    logger.info("\n--- Populating Data ---")
    total_items = 0
    for key, items in data_sets:
        container_name, _ = CONTAINERS[key]
        container = database.get_container_client(container_name)
        count = upsert_items(container, items)
        logger.info(f"  {container_name}: {count} items")
        total_items += count

    logger.info("\n" + "=" * 60)
    logger.info(f"COMPLETE: {total_items} total items populated across {len(CONTAINERS)} containers")
    logger.info("=" * 60)

    # Summary
    logger.info("\n--- Container Summary ---")
    for key, (container_name, partition_key) in CONTAINERS.items():
        logger.info(f"  {container_name} (partition: {partition_key})")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Import CargoLensX data directly into Twenty PostgreSQL database.
"""

import sqlite3
import psycopg2
import json
import uuid
from datetime import datetime
import os

# Configuration
SQLITE_DB = os.path.expanduser("~/workspace/dingxin/cargolensx-mini-query/data/cargolensx-round2.db")
PG_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "default",
    "user": "postgres",
    "password": "postgres"
}

# Get workspace schema
WORKSPACE_SCHEMA = "workspace_3ixj3i1a5avy16ptijtb3lae3"

def get_workspace_member_id(pg_cursor):
    """Get the first workspace member ID for created_by fields."""
    pg_cursor.execute(f"""
        SELECT id FROM "{WORKSPACE_SCHEMA}"."workspaceMember"
        LIMIT 1
    """)
    result = pg_cursor.fetchone()
    return result[0] if result else None

def import_companies(sqlite_conn, pg_conn, workspace_member_id):
    """Import companies from SQLite to Twenty."""
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    sqlite_cursor.execute("SELECT * FROM companies")
    companies = sqlite_cursor.fetchall()

    # Get column names
    column_names = [description[0] for description in sqlite_cursor.description]

    print(f"Importing {len(companies)} companies...")

    company_id_map = {}  # Map SQLite uuid to Twenty company ID

    for i, row in enumerate(companies):
        data = dict(zip(column_names, row))

        # Generate new UUID for Twenty
        company_id = str(uuid.uuid4())
        old_uuid = data['uuid']
        company_id_map[old_uuid] = company_id

        # Map SQLite fields to Twenty company fields
        name = data.get('name') or 'Unknown Company'
        address = data.get('address') or ''

        # Parse address into components (simple split by comma)
        address_parts = [p.strip() for p in address.split(',')] if address else []
        street1 = address_parts[0] if len(address_parts) > 0 else None
        city = address_parts[-2] if len(address_parts) > 2 else None
        country = address_parts[-1] if len(address_parts) > 1 else None

        now = datetime.utcnow()

        try:
            pg_cursor.execute(f"""
                INSERT INTO "{WORKSPACE_SCHEMA}"."company"
                ("id", "createdAt", "updatedAt", "name",
                 "addressAddressStreet1", "addressAddressCity", "addressAddressCountry",
                 "createdByWorkspaceMemberId", "updatedByWorkspaceMemberId")
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                company_id,
                now,
                now,
                name,
                street1,
                city,
                country,
                workspace_member_id,
                workspace_member_id
            ))

            if (i + 1) % 100 == 0:
                print(f"  Imported {i + 1}/{len(companies)} companies...")
                pg_conn.commit()

        except Exception as e:
            print(f"Error importing company {name}: {e}")
            continue

    pg_conn.commit()
    print(f"Successfully imported {len(company_id_map)} companies")
    return company_id_map

def import_shipping_records(sqlite_conn, pg_conn, company_id_map, workspace_member_id):
    """Import shipping records - we'll create a custom object for this."""
    sqlite_cursor = sqlite_conn.cursor()

    sqlite_cursor.execute("SELECT COUNT(*) FROM shipping_records")
    count = sqlite_cursor.fetchone()[0]
    print(f"Found {count} shipping records to import")

    # For now, just report - shipping records would need a custom object in Twenty
    print("Note: Shipping records require creating a custom object in Twenty.")
    print("You can create a 'Shipment' object in Settings > Data Model to store these.")

    # Sample query to show structure
    sqlite_cursor.execute("SELECT * FROM shipping_records LIMIT 1")
    sample = sqlite_cursor.fetchone()
    columns = [desc[0] for desc in sqlite_cursor.description]
    print(f"\nShipping record columns: {columns}")

def main():
    print("=== CargoLensX to Twenty Import ===\n")

    # Connect to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    print(f"Connected to SQLite: {SQLITE_DB}")

    # Connect to PostgreSQL
    pg_conn = psycopg2.connect(**PG_CONFIG)
    print(f"Connected to PostgreSQL: {PG_CONFIG['database']}")

    # Get workspace member ID
    pg_cursor = pg_conn.cursor()
    workspace_member_id = get_workspace_member_id(pg_cursor)

    if not workspace_member_id:
        print("ERROR: No workspace member found. Please sign in to Twenty first.")
        return

    print(f"Using workspace member: {workspace_member_id}")

    # Import companies
    company_id_map = import_companies(sqlite_conn, pg_conn, workspace_member_id)

    # Import shipping records (info only for now)
    import_shipping_records(sqlite_conn, pg_conn, company_id_map, workspace_member_id)

    # Close connections
    sqlite_conn.close()
    pg_conn.close()

    print("\n=== Import Complete ===")
    print(f"Imported {len(company_id_map)} companies")
    print("Refresh the Twenty UI to see the imported data.")

if __name__ == "__main__":
    main()
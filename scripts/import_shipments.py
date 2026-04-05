#!/usr/bin/env python3
"""
Import CargoLensX shipping records into Twenty as a custom table.
"""

import sqlite3
import psycopg2
import json
import uuid
from datetime import datetime, timezone
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

WORKSPACE_SCHEMA = "workspace_3ixj3i1a5avy16ptijtb3lae3"

def get_company_id_map(sqlite_conn, pg_cursor):
    """Build a map of SQLite company uuid to Twenty company ID."""
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute("SELECT uuid, name FROM companies")

    # Get all company names from Twenty
    pg_cursor.execute(f"""
        SELECT id, name FROM "{WORKSPACE_SCHEMA}".company
    """)
    twenty_companies = {row[1]: row[0] for row in pg_cursor.fetchall()}

    # Map SQLite uuid to Twenty ID by name matching
    id_map = {}
    for row in sqlite_cursor.fetchall():
        sqlite_uuid, name = row
        if name in twenty_companies:
            id_map[sqlite_uuid] = twenty_companies[name]

    return id_map

def create_shipment_table(pg_cursor):
    """Create the shipment table if it doesn't exist."""
    pg_cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS "{WORKSPACE_SCHEMA}"._shipment (
            id UUID PRIMARY KEY,
            "createdAt" TIMESTAMP WITH TIME ZONE,
            "updatedAt" TIMESTAMP WITH TIME ZONE,
            master_bill_no TEXT,
            sub_bill_no TEXT,
            container_no TEXT,
            vessel_name TEXT,
            supplier TEXT,
            buyer TEXT,
            quantity DOUBLE PRECISION,
            weight DOUBLE PRECISION,
            prod_desc TEXT,
            orig_port TEXT,
            dest_port TEXT,
            orig_country TEXT,
            dest_country TEXT,
            date TEXT,
            hs_code TEXT,
            trans_type TEXT,
            carrier_name TEXT,
            company_id UUID,
            others JSONB
        )
    """)
    print("Created _shipment table")

def import_shipping_records(sqlite_conn, pg_conn, company_id_map):
    """Import shipping records from SQLite to Twenty."""
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    # Create table
    create_shipment_table(pg_cursor)
    pg_conn.commit()

    sqlite_cursor.execute("SELECT * FROM shipping_records")
    records = sqlite_cursor.fetchall()
    column_names = [desc[0] for desc in sqlite_cursor.description]

    print(f"Importing {len(records)} shipping records...")

    imported = 0
    for i, row in enumerate(records):
        data = dict(zip(column_names, row))

        # Generate new UUID
        shipment_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Look up company ID
        company_uid = data.get('company_uid')
        company_id = None
        # The company_uid in SQLite is actually the 'uid' field, not 'uuid'

        try:
            pg_cursor.execute(f"""
                INSERT INTO "{WORKSPACE_SCHEMA}"._shipment
                (id, "createdAt", "updatedAt",
                 master_bill_no, sub_bill_no, container_no, vessel_name,
                 supplier, buyer, quantity, weight, prod_desc,
                 orig_port, dest_port, orig_country, dest_country,
                 date, hs_code, trans_type, carrier_name,
                 company_id, others)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                shipment_id, now, now,
                data.get('master_bill_no'),
                data.get('sub_bill_no'),
                data.get('container_no'),
                data.get('vessel_name'),
                data.get('supplier'),
                data.get('buyer'),
                data.get('quantity'),
                data.get('weight'),
                data.get('prod_desc'),
                data.get('orig_port'),
                data.get('dest_port'),
                data.get('orig_country'),
                data.get('dest_country'),
                data.get('date'),
                data.get('hs_code'),
                data.get('trans_type'),
                data.get('carrier_name'),
                company_id,
                json.dumps(data.get('others')) if data.get('others') else None
            ))
            imported += 1

            if (i + 1) % 500 == 0:
                print(f"  Imported {i + 1}/{len(records)} records...")
                pg_conn.commit()

        except Exception as e:
            print(f"Error importing record {data.get('id')}: {e}")
            continue

    pg_conn.commit()
    print(f"Successfully imported {imported} shipping records")

def main():
    print("=== Import Shipping Records to Twenty ===\n")

    sqlite_conn = sqlite3.connect(SQLITE_DB)
    pg_conn = psycopg2.connect(**PG_CONFIG)
    pg_cursor = pg_conn.cursor()

    print(f"Connected to databases")

    # Get company ID map
    print("Building company ID map...")
    company_id_map = get_company_id_map(sqlite_conn, pg_cursor)
    print(f"Found {len(company_id_map)} company mappings")

    # Import shipping records
    import_shipping_records(sqlite_conn, pg_conn, company_id_map)

    sqlite_conn.close()
    pg_conn.close()

    print("\n=== Import Complete ===")

if __name__ == "__main__":
    main()
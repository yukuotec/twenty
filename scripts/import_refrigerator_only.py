#!/usr/bin/env python3
"""
Re-import only refrigerator container business companies from CargoLensX.
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

# Keywords for refrigerator/reefer business
REFRIGERATOR_KEYWORDS = [
    'refrig', 'reefer', 'frozen', 'cold chain', 'refrigerant',
    'refrigeration', 'freezer', 'chiller', 'cool storage',
    'temperature controlled', 'cold storage', 'ice maker',
    'cold room', 'compressor', 'heat pump'
]

def clear_imported_data(pg_conn):
    """Clear all imported data from Twenty."""
    pg_cursor = pg_conn.cursor()

    print("Clearing existing data...")

    # Drop shipment table
    pg_cursor.execute(f'DROP TABLE IF EXISTS "{WORKSPACE_SCHEMA}"._shipment')
    print("  Dropped _shipment table")

    # Clear companies (except seed data - those with IDs starting with 20202020)
    pg_cursor.execute(f"""
        DELETE FROM "{WORKSPACE_SCHEMA}".company
        WHERE CAST(id AS TEXT) NOT LIKE '20202020-%'
    """)
    deleted_companies = pg_cursor.rowcount
    print(f"  Deleted {deleted_companies} companies")

    pg_conn.commit()
    return deleted_companies

def get_refrigerator_companies(sqlite_conn):
    """Get companies with refrigerator-related business."""
    sqlite_cursor = sqlite_conn.cursor()

    # Build LIKE conditions
    like_conditions = " OR ".join([f"prod_desc LIKE '%{kw}%'" for kw in REFRIGERATOR_KEYWORDS])

    # Find companies with refrigerator-related shipping records
    query = f"""
        SELECT DISTINCT c.uuid, c.name, c.uid, c.address, c.ports, c.tran_types,
               COUNT(*) as record_count
        FROM companies c
        JOIN shipping_records sr ON sr.company_uid = c.uid
        WHERE {like_conditions}
        GROUP BY c.uuid, c.name, c.uid, c.address, c.ports, c.tran_types
        ORDER BY record_count DESC
    """

    sqlite_cursor.execute(query)
    companies = sqlite_cursor.fetchall()

    print(f"Found {len(companies)} refrigerator-related companies")
    return companies

def get_shipping_records_for_companies(sqlite_conn, company_uids):
    """Get shipping records for specific companies."""
    sqlite_cursor = sqlite_conn.cursor()

    placeholders = ",".join(["?" for _ in company_uids])
    query = f"""
        SELECT * FROM shipping_records
        WHERE company_uid IN ({placeholders})
    """

    sqlite_cursor.execute(query, company_uids)
    records = sqlite_cursor.fetchall()
    column_names = [desc[0] for desc in sqlite_cursor.description]

    return records, column_names

def get_workspace_member_id(pg_cursor):
    """Get the first workspace member ID."""
    pg_cursor.execute(f"""
        SELECT id FROM "{WORKSPACE_SCHEMA}"."workspaceMember"
        LIMIT 1
    """)
    result = pg_cursor.fetchone()
    return result[0] if result else None

def import_companies(companies, pg_conn, workspace_member_id):
    """Import companies to Twenty."""
    pg_cursor = pg_conn.cursor()

    print(f"Importing {len(companies)} refrigerator companies...")

    company_id_map = {}
    now = datetime.now(timezone.utc)

    for i, row in enumerate(companies):
        uuid_str, name, uid, address, ports, tran_types, record_count = row

        company_id = str(uuid.uuid4())
        company_id_map[uid] = company_id

        address_parts = [p.strip() for p in (address or '').split(',')]
        street1 = address_parts[0] if len(address_parts) > 0 else None
        city = address_parts[-2] if len(address_parts) > 2 else None
        country = address_parts[-1] if len(address_parts) > 1 else None

        try:
            pg_cursor.execute(f"""
                INSERT INTO "{WORKSPACE_SCHEMA}"."company"
                ("id", "createdAt", "updatedAt", "name",
                 "addressAddressStreet1", "addressAddressCity", "addressAddressCountry",
                 "createdByWorkspaceMemberId", "updatedByWorkspaceMemberId")
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                company_id, now, now, name,
                street1, city, country,
                workspace_member_id, workspace_member_id
            ))

            if (i + 1) % 50 == 0:
                print(f"  Imported {i + 1}/{len(companies)} companies...")
                pg_conn.commit()

        except Exception as e:
            print(f"Error importing company {name}: {e}")
            continue

    pg_conn.commit()
    print(f"Successfully imported {len(company_id_map)} companies")
    return company_id_map

def create_shipment_table(pg_cursor):
    """Create the shipment table."""
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

def import_shipping_records(records, column_names, pg_conn, company_id_map):
    """Import shipping records."""
    pg_cursor = pg_conn.cursor()

    create_shipment_table(pg_cursor)
    pg_conn.commit()

    print(f"Importing {len(records)} shipping records...")

    imported = 0
    now = datetime.now(timezone.utc)

    for i, row in enumerate(records):
        data = dict(zip(column_names, row))

        shipment_id = str(uuid.uuid4())
        company_uid = data.get('company_uid')
        company_id = company_id_map.get(company_uid)

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

            if (i + 1) % 100 == 0:
                print(f"  Imported {i + 1}/{len(records)} records...")
                pg_conn.commit()

        except Exception as e:
            continue

    pg_conn.commit()
    print(f"Successfully imported {imported} shipping records")

def main():
    print("=== Import Refrigerator Container Business Data ===\n")

    # Connect to databases
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    pg_conn = psycopg2.connect(**PG_CONFIG)

    print(f"Connected to databases\n")

    # Get workspace member
    pg_cursor = pg_conn.cursor()
    workspace_member_id = get_workspace_member_id(pg_cursor)
    print(f"Workspace member: {workspace_member_id}\n")

    # Clear existing data
    clear_imported_data(pg_conn)
    print()

    # Get refrigerator companies
    companies = get_refrigerator_companies(sqlite_conn)

    if not companies:
        print("No refrigerator companies found!")
        return

    # Get company UIDs for shipping records
    company_uids = [c[2] for c in companies]  # uid is at index 2

    # Import companies
    company_id_map = import_companies(companies, pg_conn, workspace_member_id)

    # Get and import shipping records
    records, column_names = get_shipping_records_for_companies(sqlite_conn, company_uids)
    import_shipping_records(records, column_names, pg_conn, company_id_map)

    # Close connections
    sqlite_conn.close()
    pg_conn.close()

    print("\n=== Import Complete ===")
    print(f"Companies: {len(company_id_map)}")
    print(f"Shipping Records: {len(records)}")

if __name__ == "__main__":
    main()
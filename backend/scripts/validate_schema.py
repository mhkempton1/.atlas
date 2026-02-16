import sys
import os
import argparse
from sqlalchemy import create_engine, inspect
from sqlalchemy.schema import CreateTable

# Add backend to path so we can import services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.models import Base
from core.config import settings

def compare_types(expected_col, actual_col_info):
    """
    Compare expected SQLAlchemy column type with actual column type from inspection.
    This is a heuristic comparison as types can vary by dialect.
    """
    expected_type = expected_col.type
    actual_type = actual_col_info['type']

    # Simple string comparison of the type class name
    # e.g., String vs VARCHAR, Integer vs INTEGER
    expected_type_name = type(expected_type).__name__.upper()
    actual_type_name = type(actual_type).__name__.upper()

    # Mappings for SQLite
    if expected_type_name == 'STRING' and actual_type_name in ('VARCHAR', 'TEXT'):
        return True
    if expected_type_name == 'TEXT' and actual_type_name in ('TEXT', 'VARCHAR'):
        return True
    if expected_type_name == 'INTEGER' and actual_type_name == 'INTEGER':
        return True
    if expected_type_name == 'BOOLEAN' and actual_type_name in ('BOOLEAN', 'INTEGER'): # SQLite uses INTEGER for BOOLEAN
        return True
    if expected_type_name == 'DATETIME' and actual_type_name in ('DATETIME', 'TIMESTAMP', 'VARCHAR'): # SQLite can store dates as strings
         return True
    if expected_type_name == 'FLOAT' and actual_type_name == 'FLOAT':
        return True
    if expected_type_name == 'JSON' and actual_type_name in ('JSON', 'TEXT', 'VARCHAR'): # SQLite JSON is stored as text
        return True

    # Strict comparison if not handled above
    if str(expected_type) == str(actual_type):
        return True

    return False

def validate_schema():
    print(f"Connecting to database at {settings.DATABASE_URL}...")
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)

    actual_tables = set(inspector.get_table_names())
    expected_tables = set(Base.metadata.tables.keys())

    missing_tables = expected_tables - actual_tables
    extra_tables = actual_tables - expected_tables

    mismatches = []

    print("\n--- Schema Validation Report ---\n")

    if missing_tables:
        print(f"MISSING TABLES: {', '.join(missing_tables)}")
        mismatches.append(f"Missing tables: {missing_tables}")

    if extra_tables:
        print(f"EXTRA TABLES: {', '.join(extra_tables)}")
        mismatches.append(f"Extra tables: {extra_tables}")

    for table_name in expected_tables:
        if table_name not in actual_tables:
            continue

        print(f"Checking table: {table_name}")

        # Check Columns
        actual_columns = {col['name']: col for col in inspector.get_columns(table_name)}
        expected_columns = Base.metadata.tables[table_name].columns

        for col_name, expected_col in expected_columns.items():
            if col_name not in actual_columns:
                print(f"  MISSING COLUMN: {col_name}")
                mismatches.append(f"Table {table_name}: Missing column {col_name}")
            else:
                actual_col = actual_columns[col_name]
                # Compare types (simplified)
                if not compare_types(expected_col, actual_col):
                    print(f"  TYPE MISMATCH: {col_name} (Expected {expected_col.type}, Got {actual_col['type']})")
                    mismatches.append(f"Table {table_name}: Column {col_name} type mismatch")

        for col_name in actual_columns:
            if col_name not in expected_columns:
                print(f"  EXTRA COLUMN: {col_name}")
                mismatches.append(f"Table {table_name}: Extra column {col_name}")

        # Check Indexes
        actual_indexes = {idx['name'] for idx in inspector.get_indexes(table_name)}
        # Add primary key index if it exists explicitly or implicitly (some DBs list PK as index, some don't)
        # We focus on explicit indexes defined in the model

        # Expected indexes from model
        # Base.metadata.tables[table_name].indexes gives Index objects
        expected_indexes = set()
        for idx in Base.metadata.tables[table_name].indexes:
            if idx.name:
                expected_indexes.add(idx.name)

        # Also check column-level index=True, which creates an index named ix_tablename_colname usually
        # But SQLAlchemy naming convention might vary.
        # Let's inspect the expected indexes more carefully.
        # The 'indexes' collection on the Table object contains all indexes including those from Column(index=True)

        # However, the naming convention for auto-generated indexes is typically 'ix_<table_>_<col>'
        # We should check if an index exists on the column(s).

        # Let's stick to reporting missing named indexes if we can match names,
        # or checking if indexed columns are indeed indexed.

        # Simplified Index Check:
        # For each index in the model, check if an index with that name exists OR
        # if there is an index covering the same columns.

        for expected_idx in Base.metadata.tables[table_name].indexes:
            # Try to match by name first
            if expected_idx.name and expected_idx.name in actual_indexes:
                continue

            # If name mismatch, check columns.
            # expected_idx.columns is a collection of Column objects
            expected_col_names = [c.name for c in expected_idx.columns]

            found = False
            for actual_idx_info in inspector.get_indexes(table_name):
                if actual_idx_info['column_names'] == expected_col_names:
                    found = True
                    break

            if not found:
                print(f"  MISSING INDEX: on columns {expected_col_names}")
                mismatches.append(f"Table {table_name}: Missing index on {expected_col_names}")

    print("\n--------------------------------")

    if not mismatches and not missing_tables:
        print("Schema OK")
        return True
    else:
        print("Schema MISMATCHES FOUND")
        return False

if __name__ == "__main__":
    if validate_schema():
        sys.exit(0)
    else:
        sys.exit(1)

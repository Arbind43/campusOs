"""
Setup Neon database with all required tables.
Run with: python setup_neon_db.py
"""
import asyncio
import asyncpg
from pathlib import Path


async def main():
    # Read connection details from .env
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    database_url = os.getenv("DATABASE_URL", "")
    
    # Convert asyncpg URL to standard PostgreSQL URL for asyncpg.connect
    # From: postgresql+asyncpg://user:pass@host:port/db?ssl=require
    # To: postgresql://user:pass@host:port/db?ssl=require
    conn_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    print("=" * 70)
    print("NEON DATABASE SETUP")
    print("=" * 70)
    print(f"Connecting to Neon database...")
    print()
    
    try:
        # Connect to database
        conn = await asyncpg.connect(conn_url)
        print("✅ Connected to Neon database!")
        print()
        
        # Read SQL file
        sql_file = Path(__file__).parent.parent / "neon_setup.sql"
        with open(sql_file, "r", encoding="utf-8") as f:
            sql_script = f.read()
        
        print("📄 Executing SQL script...")
        print()
        
        # Execute SQL script
        await conn.execute(sql_script)
        
        print("✅ Database tables created successfully!")
        print()
        
        # Check tables
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        
        print(f"📊 Created {len(tables)} tables:")
        for table in tables:
            print(f"   - {table['table_name']}")
        print()
        
        # Count departments
        dept_count = await conn.fetchval("SELECT COUNT(*) FROM departments")
        print(f"✅ Seeded {dept_count} departments")
        
        # Count roles
        role_count = await conn.fetchval("SELECT COUNT(*) FROM roles")
        print(f"✅ Seeded {role_count} roles")
        
        await conn.close()
        
        print()
        print("=" * 70)
        print("NEXT STEP: Create admin user")
        print("=" * 70)
        print("Run: python -m scripts.create_admin_simple")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("Make sure:")
        print("1. .env file has correct DATABASE_URL")
        print("2. Neon database is accessible")
        print("3. You have write permissions")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

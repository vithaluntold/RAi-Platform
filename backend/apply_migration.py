"""Apply schema changes to local database directly."""
from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    # Create ProviderType enum
    conn.execute(text("""
        DO $$ BEGIN
            CREATE TYPE providertype AS ENUM ('EXTERNAL', 'ON_PREM', 'HYBRID');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """))

    # Add COMPLIANCE_ANALYSIS to agenttype enum
    conn.execute(text("ALTER TYPE agenttype ADD VALUE IF NOT EXISTS 'COMPLIANCE_ANALYSIS'"))
    conn.commit()

    # Add new columns
    conn.execute(text("ALTER TABLE agents ADD COLUMN IF NOT EXISTS provider_type providertype NOT NULL DEFAULT 'EXTERNAL'"))
    conn.execute(text("ALTER TABLE agents ADD COLUMN IF NOT EXISTS external_url VARCHAR(500)"))
    conn.execute(text("ALTER TABLE agents ADD COLUMN IF NOT EXISTS version VARCHAR(50) NOT NULL DEFAULT '1.0.0'"))

    # Widen description
    conn.execute(text("ALTER TABLE agents ALTER COLUMN description TYPE VARCHAR(2000)"))

    # Add index
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_agents_provider ON agents (provider_type)"))
    conn.commit()

    # Verify
    result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='agents' ORDER BY ordinal_position"))
    cols = [r[0] for r in result]
    print("Columns after migration:", cols)
    print("Done!")

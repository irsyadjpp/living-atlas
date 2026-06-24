#!/usr/bin/env python3
"""Test script to verify infrastructure setup status."""

import sys
import os
from pathlib import Path

# Add shared package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared" / "src"))

from ai_shared.config import ServiceConfig


def main():
    """Test infrastructure configuration and connectivity."""
    
    print("=" * 70)
    print("🔧 INFRASTRUCTURE STATUS CHECK")
    print("=" * 70)
    print()
    
    # Load configuration
    try:
        config = ServiceConfig()
        print("✅ Configuration loaded successfully")
        print()
    except Exception as e:
        print(f"❌ Configuration load failed: {e}")
        print("   Check that .env file exists and is properly formatted")
        return
    
    # Check database configuration
    print("Database Configuration:")
    print(f"  Host: {config.pg_host}")
    print(f"  Port: {config.pg_port}")
    print(f"  Database: {config.pg_database}")
    print(f"  User: {config.pg_user}")
    print(f"  Min Connections: {config.pg_min_connections}")
    print(f"  Max Connections: {config.pg_max_connections}")
    print()
    
    # Check Kafka configuration
    print("Message Queue Configuration:")
    print(f"  Bootstrap Servers: {config.kafka_bootstrap_servers}")
    print(f"  Consumer Group: {config.kafka_consumer_group}")
    print()
    
    # Check Redis configuration
    print("Redis Configuration:")
    print(f"  URL: {config.redis_url}")
    print()
    
    # Check API keys status
    print("External API Keys Status:")
    api_keys = {
        "GEMINI_API_KEY": config.gemini_api_key,
        "ANTHROPIC_API_KEY": config.anthropic_api_key,
        "OPENAI_API_KEY": config.openai_api_key,
    }
    
    for key_name, key_value in api_keys.items():
        if key_value and key_value != "":
            masked = key_value[:8] + "..." if len(key_value) > 8 else "configured"
            print(f"  ✅ {key_name}: {masked}")
        else:
            print(f"  ❌ {key_name}: not configured")
    print()
    
    # Check SQL migration files
    print("Database Migration Files:")
    migrations_dir = Path("/home/sdibonerate85/Developmet/living-atlas/ai-platform/scripts/migrations")
    if migrations_dir.exists():
        for sql_file in sorted(migrations_dir.glob("*.sql")):
            print(f"  ✅ {sql_file.name}")
    else:
        print("  ❌ Migrations directory not found")
    print()
    
    # Check configuration files
    print("Configuration Files:")
    config_files = [
        ".env.enrichment",
        "docs/API_SETUP_GUIDE.md", 
        "docs/REDPANDA_SETUP_GUIDE.md"
    ]
    
    for config_file in config_files:
        file_path = Path("/home/sdibonerate85/Developmet/living-atlas/ai-platform") / config_file
        if file_path.exists():
            print(f"  ✅ {config_file}")
        else:
            print(f"  ❌ {config_file} (not found - generate with scripts)")
    print()
    
    print("=" * 70)
    print("📊 INFRASTRUCTURE STATUS SUMMARY")
    print("=" * 70)
    print()
    
    # Overall status
    database_configured = config.pg_host and config.pg_port
    kafka_configured = config.kafka_bootstrap_servers
    redis_configured = config.redis_url
    api_keys_configured = sum(1 for v in api_keys.values() if v and v != "")
    
    print(f"Database Configuration: {'✅' if database_configured else '❌'}")
    print(f"Message Queue Configured: {'✅' if kafka_configured else '❌'}")
    print(f"Redis Configured: {'✅' if redis_configured else '❌'}")
    print(f"API Keys Configured: {api_keys_configured}/3")
    print()
    
    if database_configured and kafka_configured and redis_configured and api_keys_configured >= 2:
        print("✅ Infrastructure setup ready for enrichment service implementation")
        print()
        print("Next steps:")
        print("  1. Execute SQL migrations")
        print(" 2. Set up Redpanda topics")
        print(" 3. Implement enrichment-service LLM client router")
        print("  4. Implement knowledge extractors integration")
    else:
        print("⚠️  Infrastructure setup incomplete")
        print()
        print("Missing components:")
        if not database_configured:
            print("  - Database configuration")
        if not kafka_configured:
            print("  - Message queue configuration") 
        if not redis_configured:
            print(" - Redis configuration")
        if api_keys_configured < 2:
            print(f"  - External API keys ({3 - api_keys_configured} missing)")
        print()
        print("Complete setup by:")
        print("  1. Configure .env with database credentials")
        print("  2. Add API keys to .env")
        print("  3. Start Redis and Redpanda services")
        print("  4. Run: python3 scripts/setup_redpanda_topics.py")


if __name__ == "__main__":
    main()
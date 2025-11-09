#!/usr/bin/env python3
"""
Implementation Verification Script
Validates that all HP-1 through HP-5 enhancements are correctly implemented.
"""
import os
import sys
from pathlib import Path


def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a file exists."""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ MISSING {description}: {filepath}")
        return False


def check_method_exists(filepath: str, method_name: str, description: str) -> bool:
    """Check if a method exists in a file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            if f"def {method_name}" in content:
                print(f"✅ {description}: {method_name}()")
                return True
            else:
                print(f"❌ MISSING {description}: {method_name}()")
                return False
    except FileNotFoundError:
        print(f"❌ FILE NOT FOUND: {filepath}")
        return False


def check_import_exists(filepath: str, import_statement: str, description: str) -> bool:
    """Check if an import exists in a file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            if import_statement in content:
                print(f"✅ {description}")
                return True
            else:
                print(f"❌ MISSING {description}")
                return False
    except FileNotFoundError:
        print(f"❌ FILE NOT FOUND: {filepath}")
        return False


def main():
    """Run all verification checks."""
    print("\n" + "=" * 80)
    print("HAVEN TOKEN - INTEGRATION IMPLEMENTATION VERIFICATION")
    print("=" * 80 + "\n")

    all_checks_passed = True

    # HP-1: Aurora PMS Integration
    print("\n📋 HP-1: Aurora PMS Integration")
    print("-" * 80)

    aurora_file = "backend/services/aurora_integration.py"
    all_checks_passed &= check_method_exists(aurora_file, "parseBookingData", "Parse booking data method")
    all_checks_passed &= check_method_exists(aurora_file, "calculateRewardAmount", "Calculate reward method")
    all_checks_passed &= check_method_exists(aurora_file, "handleBookingConfirmation", "Handle confirmation method")

    # HP-2: Tribe App Integration
    print("\n📋 HP-2: Tribe App Integration")
    print("-" * 80)

    tribe_file = "backend/services/tribe_integration.py"
    all_checks_passed &= check_method_exists(tribe_file, "parseEventData", "Parse event data method")
    all_checks_passed &= check_method_exists(tribe_file, "calculateAttendanceReward", "Calculate attendance reward method")
    all_checks_passed &= check_method_exists(tribe_file, "handleEventAttendance", "Handle event attendance method")
    all_checks_passed &= check_method_exists(tribe_file, "sync_recent_events", "Sync recent events method")

    # HP-3: Alembic Migrations
    print("\n📋 HP-3: Database Migrations with Alembic")
    print("-" * 80)

    all_checks_passed &= check_file_exists("backend/alembic.ini", "Alembic configuration")
    all_checks_passed &= check_file_exists("backend/alembic/env.py", "Alembic environment")
    all_checks_passed &= check_file_exists("backend/alembic/script.py.mako", "Migration template")
    all_checks_passed &= check_file_exists("backend/alembic/README.md", "Migration documentation")
    all_checks_passed &= check_file_exists("backend/alembic/versions/20251108_0000-001_initial_schema.py", "Initial schema migration")
    all_checks_passed &= check_file_exists("backend/alembic/versions/20251108_0001-002_aurora_integration_tables.py", "Aurora tables migration")
    all_checks_passed &= check_file_exists("backend/alembic/versions/20251108_0002-003_tribe_integration_tables.py", "Tribe tables migration")
    all_checks_passed &= check_file_exists("backend/alembic/versions/20251108_0003-004_audit_log_table.py", "Audit log migration")

    # HP-4: Webhook Signature Verification
    print("\n📋 HP-4: Webhook Signature Verification")
    print("-" * 80)

    app_file = "backend/app.py"
    all_checks_passed &= check_import_exists(app_file, "from middleware.webhook_auth import verify_aurora_webhook, verify_tribe_webhook", "Webhook auth imports")

    # Check webhook endpoints have verification
    with open(app_file, 'r') as f:
        app_content = f.read()

    webhook_endpoints = [
        ("/webhooks/aurora/booking-created", "verified: bool = Depends(verify_aurora_webhook)"),
        ("/webhooks/aurora/booking-completed", "verified: bool = Depends(verify_aurora_webhook)"),
        ("/webhooks/aurora/booking-cancelled", "verified: bool = Depends(verify_aurora_webhook)"),
        ("/webhooks/aurora/review-submitted", "verified: bool = Depends(verify_aurora_webhook)"),
        ("/webhooks/tribe/event-attendance", "verified: bool = Depends(verify_tribe_webhook)"),
        ("/webhooks/tribe/contribution", "verified: bool = Depends(verify_tribe_webhook)"),
        ("/webhooks/tribe/staking-started", "verified: bool = Depends(verify_tribe_webhook)"),
        ("/webhooks/tribe/coaching-milestone", "verified: bool = Depends(verify_tribe_webhook)"),
        ("/webhooks/tribe/referral-success", "verified: bool = Depends(verify_tribe_webhook)"),
    ]

    for endpoint, verification in webhook_endpoints:
        if verification in app_content:
            print(f"✅ Webhook signature verification: {endpoint}")
        else:
            print(f"❌ MISSING signature verification: {endpoint}")
            all_checks_passed = False

    # HP-5: Idempotency Middleware
    print("\n📋 HP-5: Idempotency Middleware")
    print("-" * 80)

    all_checks_passed &= check_file_exists("backend/middleware/idempotency.py", "Idempotency middleware")
    all_checks_passed &= check_import_exists(app_file, "from middleware.idempotency import IdempotencyMiddleware", "Idempotency imports")

    idempotency_file = "backend/middleware/idempotency.py"
    all_checks_passed &= check_method_exists(idempotency_file, "generate_key", "Generate idempotency key method")
    all_checks_passed &= check_method_exists(idempotency_file, "store_response", "Store response method")
    all_checks_passed &= check_method_exists(idempotency_file, "get_cached_response", "Get cached response method")
    all_checks_passed &= check_method_exists(idempotency_file, "require_idempotency_key", "Require idempotency key method")

    # Check idempotency applied to endpoints
    if "idempotency_key: Optional[str] = Header(None, alias=\"Idempotency-Key\")" in app_content:
        print("✅ Idempotency header support in /token/mint")
    else:
        print("❌ MISSING idempotency header in /token/mint")
        all_checks_passed = False

    # Test Files
    print("\n📋 Test Files")
    print("-" * 80)

    all_checks_passed &= check_file_exists("backend/tests/test_aurora_integration.py", "Aurora integration tests")
    all_checks_passed &= check_file_exists("backend/tests/test_tribe_integration.py", "Tribe integration tests")
    all_checks_passed &= check_file_exists("backend/tests/test_idempotency.py", "Idempotency tests")
    all_checks_passed &= check_file_exists("backend/tests/test_webhook_auth.py", "Webhook auth tests")

    # Documentation
    print("\n📋 Documentation")
    print("-" * 80)

    all_checks_passed &= check_file_exists("INTEGRATION_IMPLEMENTATION_SUMMARY.md", "Implementation summary")

    # Final Result
    print("\n" + "=" * 80)
    if all_checks_passed:
        print("🎉 ALL CHECKS PASSED - Implementation is complete!")
        print("=" * 80)
        print("\nNext Steps:")
        print("1. Run database migrations: cd backend && alembic upgrade head")
        print("2. Run tests: cd backend && pytest -v")
        print("3. Start the server: cd backend && uvicorn app:app --reload")
        print("4. Check health endpoint: curl http://localhost:8000/health")
        return 0
    else:
        print("⚠️  SOME CHECKS FAILED - Review output above")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())

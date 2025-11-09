# Database Migrations with Alembic

This directory contains database migrations for the HAVEN Token backend using Alembic.

## Overview

Alembic is a database migration tool for SQLAlchemy. It provides a way to manage database schema changes in a version-controlled, repeatable manner.

## Migration Files

The `versions/` directory contains all migration scripts:

- `001_initial_schema.py` - Creates core tables (users, transactions, redemptions, metrics)
- `002_aurora_integration_tables.py` - Adds Aurora PMS booking tracking tables
- `003_tribe_integration_tables.py` - Adds Tribe app integration tables (events, rewards, staking)
- `004_audit_log_table.py` - Adds audit log table for compliance and security

## Setup

### 1. Configure Database URL

Set your database URL in environment or alembic.ini:

```bash
export DATABASE_URL="postgresql://postgres:password@localhost:5432/haven"
```

Or edit `alembic.ini`:

```ini
sqlalchemy.url = postgresql://postgres:password@localhost:5432/haven
```

### 2. Run Migrations

Apply all pending migrations:

```bash
cd backend
alembic upgrade head
```

## Common Commands

### Check Current Migration Version

```bash
alembic current
```

### View Migration History

```bash
alembic history --verbose
```

### Upgrade to Latest

```bash
alembic upgrade head
```

### Upgrade by Specific Number of Revisions

```bash
alembic upgrade +1  # Upgrade one revision
alembic upgrade +2  # Upgrade two revisions
```

### Downgrade

```bash
alembic downgrade -1     # Downgrade one revision
alembic downgrade base   # Downgrade to initial state
```

### Show SQL Without Running

```bash
alembic upgrade head --sql
```

## Creating New Migrations

### Auto-generate Migration from Model Changes

After modifying `database/models.py`:

```bash
alembic revision --autogenerate -m "description of changes"
```

### Create Empty Migration

```bash
alembic revision -m "description of changes"
```

Then manually edit the generated file in `versions/`.

## Migration Best Practices

1. **Always Review Auto-generated Migrations**
   - Alembic may not detect all changes correctly
   - Verify the upgrade() and downgrade() functions

2. **Test Migrations on Development Database First**
   ```bash
   # Create test database
   createdb haven_test

   # Run migrations
   DATABASE_URL="postgresql://postgres:password@localhost:5432/haven_test" alembic upgrade head

   # Test downgrade
   DATABASE_URL="postgresql://postgres:password@localhost:5432/haven_test" alembic downgrade base
   ```

3. **Never Modify Existing Migrations**
   - Once a migration has been applied to production, create a new migration to fix issues
   - Modifying existing migrations can cause inconsistencies

4. **Write Reversible Migrations**
   - Always implement both upgrade() and downgrade()
   - Test that migrations can be rolled back

5. **Keep Migrations Small and Focused**
   - One migration per logical change
   - Easier to debug and roll back if needed

## Database Schema Overview

### Core Tables

- `users` - User accounts with wallet addresses
- `transactions` - Token mint/burn/transfer operations
- `redemption_requests` - Token redemption for fiat payouts
- `system_metrics` - System-wide analytics and metrics

### Integration Tables

- `aurora_bookings` - Aurora PMS booking reward tracking
- `tribe_events` - Tribe app event attendance records
- `tribe_rewards` - Community contribution rewards
- `staking_records` - Token staking and rewards

### Compliance Tables

- `audit_log` - Security and compliance audit trail

## Troubleshooting

### Error: "Can't locate revision identified by..."

This means the database's migration version doesn't match the migration files.

```bash
# Check current version
alembic current

# Stamp database with current version
alembic stamp head
```

### Error: "Target database is not up to date"

Run pending migrations:

```bash
alembic upgrade head
```

### Migration Conflicts

If multiple developers create migrations simultaneously:

1. Resolve conflicts in migration files
2. Update `down_revision` to create linear history
3. Test migrations in sequence

## Production Deployment

### Pre-deployment Checklist

- [ ] Test migrations on staging database
- [ ] Backup production database
- [ ] Review migration SQL
- [ ] Plan rollback procedure
- [ ] Schedule maintenance window if needed

### Deploy Migrations

```bash
# Backup database
pg_dump haven > backup_$(date +%Y%m%d_%H%M%S).sql

# Run migrations
alembic upgrade head

# Verify
alembic current
```

### Rollback if Needed

```bash
# Rollback last migration
alembic downgrade -1

# Restore from backup if necessary
psql haven < backup_20251108_000000.sql
```

## Environment-Specific Migrations

### Development

```bash
DATABASE_URL="postgresql://localhost/haven_dev" alembic upgrade head
```

### Staging

```bash
DATABASE_URL="postgresql://staging-db/haven_staging" alembic upgrade head
```

### Production

```bash
DATABASE_URL="postgresql://prod-db/haven" alembic upgrade head
```

## Support

For issues with migrations:
1. Check Alembic documentation: https://alembic.sqlalchemy.org/
2. Review migration logs
3. Contact the development team

# LitigationOS — Disaster Recovery Procedure

## Overview

This document provides step-by-step restore procedures for LitigationOS.
All procedures have been designed to be executable by any team member.

---

## Recovery Tiers

| Tier | Scenario | RTO | RPO | Procedure |
|------|----------|-----|-----|-----------|
| T1 | Application crash | 5 min | 0 | [Restart](#t1-application-restart) |
| T2 | Database corruption | 30 min | ≤24h | [DB Restore](#t2-database-restore) |
| T3 | Server failure | 2h | ≤24h | [Full Rebuild](#t3-full-server-rebuild) |
| T4 | Complete data loss | 4h | ≤7d | [Cold Restore](#t4-cold-restore-from-weekly-backup) |

*RTO = Recovery Time Objective, RPO = Recovery Point Objective*

---

## T1: Application Restart

**Symptoms:** Web UI unresponsive, API returning 5xx errors, container stopped.

### Docker Deployment
```bash
# Check container status
docker compose ps

# Restart the web service
docker compose restart web

# If container won't start, check logs
docker compose logs web --tail 100

# Nuclear option: rebuild and restart
docker compose down
docker compose up -d --build
```

### Vercel Deployment
```bash
# Trigger redeployment
vercel --prod

# Or redeploy from dashboard:
# https://vercel.com/dashboard → Project → Deployments → Redeploy
```

### Verification
```bash
curl -s http://localhost:3000/api/health | jq .
# Expected: { "status": "ok", "database": "connected" }
```

---

## T2: Database Restore

**Symptoms:** SQLite errors, corrupted data, missing records after crash.

### Step 1: Stop the application
```bash
docker compose stop web
```

### Step 2: Check database integrity
```bash
sqlite3 data/litigationos.db "PRAGMA integrity_check;"
# If output is NOT "ok", proceed with restore
```

### Step 3: Locate latest backup
```bash
# Daily backups (most recent)
ls -la backups/daily/ | tail -5

# Weekly backups (if daily not available)
ls -la backups/weekly/ | tail -5
```

### Step 4: Restore from backup
```bash
# Preserve corrupted DB for investigation
mv data/litigationos.db data/litigationos_corrupted_$(date +%Y%m%d).db

# Restore from latest daily backup
cp backups/daily/litigationos_YYYYMMDD_HHMMSS.db data/litigationos.db

# Verify restored database
sqlite3 data/litigationos.db "PRAGMA integrity_check;"
sqlite3 data/litigationos.db "SELECT COUNT(*) FROM sqlite_master;"
```

### Step 5: Restart application
```bash
docker compose start web

# Verify
curl -s http://localhost:3000/api/health
```

---

## T3: Full Server Rebuild

**Symptoms:** Server hardware failure, VM lost, need to deploy on new machine.

### Prerequisites
- Docker and Docker Compose installed on new machine
- Access to backup storage (local or S3)
- `.env` file (stored securely outside the server)

### Step 1: Clone repository
```bash
git clone https://github.com/YOUR_ORG/LitigationOS.git
cd LitigationOS
```

### Step 2: Restore environment configuration
```bash
# Copy your backed-up .env file
cp /secure-backup/.env .env

# Or recreate from template
cp 00_SYSTEM/deploy/.env.example .env
# Edit .env with your values
```

### Step 3: Restore database backups
```bash
mkdir -p data backups

# From local backup storage
cp /backup-mount/weekly/litigationos_full_latest.db data/litigationos.db
cp /backup-mount/weekly/context_latest.db ./litigation_context.db

# From S3 (if using remote backup)
# aws s3 cp s3://litigos-backups/weekly/latest/ ./data/ --recursive
```

### Step 4: Start the full stack
```bash
cd 00_SYSTEM/deploy
docker compose up -d

# Monitor startup
docker compose logs -f
```

### Step 5: Restore Neo4j data
```bash
# If Neo4j dump exists
docker compose exec neo4j neo4j-admin database load neo4j --from-path=/backups/neo4j/

# Restart Neo4j to apply
docker compose restart neo4j
```

### Step 6: Verify
```bash
# Application health
curl -s http://localhost:3000/api/health

# Database connectivity
docker compose exec web node -e "
  const db = require('better-sqlite3')('/app/data/litigationos.db');
  console.log('Tables:', db.prepare(\"SELECT COUNT(*) as n FROM sqlite_master WHERE type='table'\").get());
  db.close();
"

# Neo4j connectivity
docker compose exec neo4j cypher-shell -u neo4j -p YOUR_PASSWORD "MATCH (n) RETURN COUNT(n)"
```

---

## T4: Cold Restore from Weekly Backup

**Symptoms:** Complete data loss, no daily backups available.

Follow T3 procedure above but use weekly backup files:
```bash
# Decompress weekly backup
gunzip backups/weekly/litigationos_full_YYYYMMDD.db.gz

# Copy to data directory
cp backups/weekly/litigationos_full_YYYYMMDD.db data/litigationos.db
```

**Note:** Up to 7 days of data may be lost. Check with team for any manual records
of evidence entered since the last weekly backup.

---

## Post-Recovery Checklist

After ANY recovery procedure:

- [ ] Verify application responds at `/api/health`
- [ ] Check database row counts match expectations
- [ ] Verify OMEGA scores are calculating
- [ ] Test evidence search functionality
- [ ] Check Neo4j graph queries return data
- [ ] Verify backup service is running
- [ ] Review application logs for errors
- [ ] Notify team of recovery completion and any data loss window

---

## Backup Verification Schedule

| Task | Frequency | Owner |
|------|-----------|-------|
| Verify daily backup exists | Daily (automated) | Backup service |
| Test restore from daily backup | Monthly | System admin |
| Test full T3 rebuild on clean VM | Quarterly | System admin |
| Review and update this document | Quarterly | Team lead |

---

## Emergency Contacts

| Role | Contact | Responsibility |
|------|---------|----------------|
| System Admin | [TBD] | Infrastructure, Docker, backups |
| Lead Developer | [TBD] | Application code, database schema |
| Legal Team Lead | [TBD] | Data loss assessment, case impact |

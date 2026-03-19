import sqlite3
c = sqlite3.connect(r'C:\Users\andre\LitigationOS\litigation_context.db').cursor()

c.execute("SELECT COUNT(*) FROM master_timeline WHERE event_date >= '2020-01-01' AND event_date <= '2026-12-31'")
print(f'Events in 2020-2026 range: {c.fetchone()[0]:,}')

c.execute("SELECT COUNT(*) FROM master_timeline WHERE event_date >= '2024-01-01' AND event_date <= '2026-12-31'")
print(f'Events in case period (2024-2026): {c.fetchone()[0]:,}')

c.execute("SELECT category, COUNT(*) FROM master_timeline WHERE event_date >= '2024-01-01' AND event_date <= '2026-12-31' GROUP BY category ORDER BY COUNT(*) DESC LIMIT 15")
print('\nCategories (2024-2026):')
for cat, cnt in c.fetchall():
    print(f'  {cat}: {cnt:,}')

c.execute("SELECT substr(event_date,1,7) as ym, COUNT(*) FROM master_timeline WHERE event_date >= '2024-01-01' AND event_date <= '2026-12-31' GROUP BY ym ORDER BY ym")
print('\nMonthly distribution:')
for ym, cnt in c.fetchall():
    bar = '#' * min(cnt // 20, 50)
    print(f'  {ym}: {cnt:4,} {bar}')

c.execute("SELECT event_date, COUNT(*) FROM master_timeline WHERE event_date >= '2024-01-01' AND event_date <= '2026-12-31' GROUP BY event_date ORDER BY COUNT(*) DESC LIMIT 10")
print('\nHottest days:')
for d, cnt in c.fetchall():
    print(f'  {d}: {cnt} events')

# Critical events
c.execute("SELECT event_date, category, title, description FROM master_timeline WHERE event_date >= '2024-01-01' AND CAST(severity AS INTEGER) >= 9 ORDER BY event_date LIMIT 30")
print('\n=== CRITICAL EVENTS (Severity 9-10) ===')
for d, cat, title, desc in c.fetchall():
    print(f'  {d} [{cat}] {title[:80]}')

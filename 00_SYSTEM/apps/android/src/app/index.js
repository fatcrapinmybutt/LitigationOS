import { View, Text, ScrollView, StyleSheet, Pressable } from 'react-native';
import { useEffect, useState } from 'react';

const COLORS = {
  bg: '#0a0e27',
  card: '#0f1338',
  border: '#1e2a5e',
  text: '#e0e7ff',
  muted: '#8b9dc3',
  accent: '#818cf8',
  critical: '#ef4444',
  high: '#f97316',
  standard: '#3b82f6',
  hold: '#6b7280',
  success: '#22c55e',
};

const LANES = [
  { id: 'A', name: 'MSC', color: '#3b82f6', forum: 'Michigan Supreme Court' },
  { id: 'B', name: 'COA', color: '#22c55e', forum: 'Court of Appeals' },
  { id: 'C', name: '14th Circuit', color: '#a855f7', forum: '14th Circuit Court' },
  { id: 'D', name: 'JTC', color: '#ef4444', forum: 'Judicial Tenure Commission' },
  { id: 'E', name: 'USDC', color: '#f97316', forum: 'US District Court' },
  { id: 'F', name: 'State Bar', color: '#eab308', forum: 'State Bar of Michigan' },
];

const OMEGA_ACTIONS = [
  { name: 'JTC Formal Complaint', score: 93, tier: 'CRITICAL', forum: 'JTC', lane: 'D' },
  { name: 'MSC Emergency Application', score: 84, tier: 'HIGH', forum: 'MSC', lane: 'A' },
  { name: 'MSC Superintending Control', score: 81, tier: 'HIGH', forum: 'MSC', lane: 'A' },
  { name: 'MSC Habeas Corpus', score: 81, tier: 'HIGH', forum: 'MSC', lane: 'A' },
  { name: 'USDC Section 1983', score: 81, tier: 'HIGH', forum: 'USDC', lane: 'E' },
  { name: 'Vacate Ex Parte Orders', score: 79, tier: 'HIGH', forum: '14th Circuit', lane: 'C' },
  { name: 'State Bar - Berry', score: 72, tier: 'HIGH', forum: 'State Bar', lane: 'F' },
  { name: 'State Bar - Barnes', score: 70, tier: 'HIGH', forum: 'State Bar', lane: 'F' },
];

function SeparationCounter() {
  const [days, setDays] = useState(0);
  useEffect(() => {
    const start = new Date('2025-08-08');
    const now = new Date();
    setDays(Math.floor((now - start) / 86400000));
  }, []);

  return (
    <View style={[styles.card, { borderColor: COLORS.critical, borderWidth: 2 }]}>
      <Text style={[styles.cardTitle, { color: COLORS.critical }]}>PARENT-CHILD SEPARATION</Text>
      <Text style={styles.bigNumber}>{days}</Text>
      <Text style={styles.muted}>days since August 8, 2025</Text>
      <Text style={[styles.muted, { marginTop: 4 }]}>Pigors v. Watson • Lincoln</Text>
    </View>
  );
}

function ForumCard({ lane }) {
  return (
    <View style={[styles.card, { borderLeftColor: lane.color, borderLeftWidth: 4 }]}>
      <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 4 }}>
        <View style={[styles.badge, { backgroundColor: lane.color + '33' }]}>
          <Text style={{ color: lane.color, fontWeight: 'bold', fontSize: 12 }}>Lane {lane.id}</Text>
        </View>
        <Text style={[styles.cardTitle, { marginLeft: 8 }]}>{lane.name}</Text>
      </View>
      <Text style={styles.muted}>{lane.forum}</Text>
    </View>
  );
}

function OmegaItem({ action }) {
  const tierColor = action.tier === 'CRITICAL' ? COLORS.critical
    : action.tier === 'HIGH' ? COLORS.high
    : COLORS.standard;

  return (
    <View style={[styles.card, { flexDirection: 'row', alignItems: 'center', paddingVertical: 12 }]}>
      <View style={[styles.scoreBadge, { backgroundColor: tierColor + '22', borderColor: tierColor }]}>
        <Text style={{ color: tierColor, fontWeight: 'bold', fontSize: 16 }}>{action.score}</Text>
      </View>
      <View style={{ flex: 1, marginLeft: 12 }}>
        <Text style={styles.text}>{action.name}</Text>
        <Text style={styles.muted}>{action.forum} • Lane {action.lane}</Text>
      </View>
      <View style={[styles.tierBadge, { backgroundColor: tierColor + '22' }]}>
        <Text style={{ color: tierColor, fontSize: 10, fontWeight: 'bold' }}>{action.tier}</Text>
      </View>
    </View>
  );
}

export default function HomeScreen() {
  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 40 }}>
      <Text style={styles.header}>LitigationOS</Text>
      <Text style={[styles.muted, { textAlign: 'center', marginBottom: 20 }]}>
        Case Intelligence Dashboard
      </Text>

      <SeparationCounter />

      <Text style={[styles.sectionTitle, { marginTop: 24 }]}>Case Forums</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 8 }}>
        {LANES.map(l => <ForumCard key={l.id} lane={l} />)}
      </ScrollView>

      <Text style={[styles.sectionTitle, { marginTop: 16 }]}>OMEGA Priority Queue</Text>
      {OMEGA_ACTIONS.map((a, i) => <OmegaItem key={i} action={a} />)}

      <View style={[styles.card, { marginTop: 24, alignItems: 'center' }]}>
        <Text style={styles.cardTitle}>System Status</Text>
        <View style={{ flexDirection: 'row', marginTop: 8 }}>
          <View style={[styles.statusDot, { backgroundColor: COLORS.success }]} />
          <Text style={styles.text}>All Systems Operational</Text>
        </View>
        <Text style={[styles.muted, { marginTop: 4 }]}>662 DB tables • 308,704 evidence quotes</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.bg, padding: 16 },
  header: { fontSize: 28, fontWeight: 'bold', color: COLORS.text, textAlign: 'center', marginTop: 8 },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', color: COLORS.text, marginBottom: 12 },
  card: { backgroundColor: COLORS.card, borderRadius: 12, padding: 16, marginBottom: 12, borderColor: COLORS.border, borderWidth: 1, marginRight: 12 },
  cardTitle: { fontSize: 14, fontWeight: 'bold', color: COLORS.text },
  text: { fontSize: 14, color: COLORS.text },
  muted: { fontSize: 12, color: COLORS.muted },
  bigNumber: { fontSize: 56, fontWeight: 'bold', color: COLORS.critical, textAlign: 'center' },
  badge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6 },
  scoreBadge: { width: 48, height: 48, borderRadius: 24, borderWidth: 2, alignItems: 'center', justifyContent: 'center' },
  tierBadge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 6 },
  statusDot: { width: 8, height: 8, borderRadius: 4, marginRight: 8, marginTop: 4 },
});

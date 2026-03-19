/**
 * DeadlineFactory — Court deadline test data.
 *
 * Matches payload schema: {id, title, dueDate, daysRemaining, severity}
 * Severity enum: critical | urgent | warning | info
 */
import { faker } from '@faker-js/faker';
import { sequence } from './sequence';

const DEADLINE_TITLES = [
  'Disqualification Motion — McNeill',
  'MSC Emergency Application',
  'COA Brief 366810',
  'JTC Formal Complaint',
  'USDC §1983 Complaint',
  'Motion for Reconsideration',
  'PPO Modification',
  'Discovery Responses Due',
  'Custody Evaluation Filing',
  'FOC Objection Window',
];

export class DeadlineFactory {
  constructor() {
    this.data = {};
  }

  static create(overrides) {
    return new DeadlineFactory().with(overrides).build();
  }

  static createMany(count, overrides) {
    return Array.from({ length: count }, () => DeadlineFactory.create(overrides));
  }

  with(overrides) {
    if (overrides) this.data = { ...this.data, ...overrides };
    return this;
  }

  withSeverity(severity) {
    this.data.severity = severity;
    return this;
  }

  asCritical() {
    this.data.severity = 'critical';
    this.data.daysRemaining = faker.number.int({ min: 1, max: 7 });
    return this;
  }

  asUrgent() {
    this.data.severity = 'urgent';
    this.data.daysRemaining = faker.number.int({ min: 8, max: 14 });
    return this;
  }

  asWarning() {
    this.data.severity = 'warning';
    this.data.daysRemaining = faker.number.int({ min: 15, max: 30 });
    return this;
  }

  asInfo() {
    this.data.severity = 'info';
    this.data.daysRemaining = faker.number.int({ min: 31, max: 90 });
    return this;
  }

  /** Trait: past due (negative days) */
  asPastDue() {
    this.data.daysRemaining = faker.number.int({ min: -30, max: -1 });
    this.data.severity = 'critical';
    return this;
  }

  /** Trait: MCR 7.204(A)(1) 21-day claim of appeal */
  asAppealDeadline() {
    this.data.title = '21-Day Claim of Appeal — MCR 7.204(A)(1)';
    this.data.severity = 'critical';
    return this;
  }

  build() {
    const n = sequence.next('deadline');
    const daysRemaining = this.data.daysRemaining ?? faker.number.int({ min: 1, max: 60 });
    const dueDate = this.data.dueDate ?? new Date(Date.now() + daysRemaining * 86400000).toISOString();

    return {
      id: this.data.id ?? `deadline-${n}`,
      title: this.data.title ?? faker.helpers.arrayElement(DEADLINE_TITLES),
      dueDate,
      daysRemaining,
      severity: this.data.severity ?? (
        daysRemaining <= 7 ? 'critical' :
        daysRemaining <= 14 ? 'urgent' :
        daysRemaining <= 30 ? 'warning' : 'info'
      ),
      ...this.data,
    };
  }
}

export default DeadlineFactory;

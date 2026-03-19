/**
 * NotificationFactory — System notification test data.
 *
 * Matches payload schema: {id, type, title, message, createdAt}
 */
import { faker } from '@faker-js/faker';
import { sequence } from './sequence';

const NOTIFICATION_TYPES = ['info', 'success', 'warning', 'error', 'deadline', 'filing', 'evidence'];

const NOTIFICATION_TEMPLATES = [
  { type: 'deadline', title: 'Deadline Approaching', message: 'Disqualification motion due in 10 days' },
  { type: 'filing', title: 'Filing Ready', message: 'MSC Emergency Application scored 92/100' },
  { type: 'evidence', title: 'Evidence Ingested', message: '47 new quotes extracted from court order' },
  { type: 'success', title: 'Pipeline Complete', message: 'Phase 4a completed — 12,450 PDFs processed' },
  { type: 'warning', title: 'Agent Crash', message: 'Agent J03 crashed during judicial analysis — retrying' },
  { type: 'error', title: 'Database Error', message: 'WAL checkpoint failed — retrying in 30s' },
  { type: 'info', title: 'System Update', message: 'MANBEARPIG v9.0 loaded — 140 methods available' },
];

export class NotificationFactory {
  constructor() {
    this.data = {};
    this.traits = [];
  }

  static create(overrides) {
    return new NotificationFactory().with(overrides).build();
  }

  static createMany(count, overrides) {
    return Array.from({ length: count }, () => NotificationFactory.create(overrides));
  }

  with(overrides) {
    if (overrides) this.data = { ...this.data, ...overrides };
    return this;
  }

  withTrait(trait) {
    this.traits.push(trait);
    return this;
  }

  /** Trait: urgent deadline notification */
  asDeadlineAlert() {
    const tpl = NOTIFICATION_TEMPLATES[0];
    this.data.type = tpl.type;
    this.data.title = tpl.title;
    return this;
  }

  /** Trait: filing readiness notification */
  asFilingReady() {
    const tpl = NOTIFICATION_TEMPLATES[1];
    this.data.type = tpl.type;
    this.data.title = tpl.title;
    return this;
  }

  /** Trait: error notification */
  asError() {
    this.data.type = 'error';
    this.data.title = 'Error';
    this.data.message = faker.lorem.sentence();
    return this;
  }

  /** Trait: read/unread */
  asRead() {
    this.data.read = true;
    return this;
  }

  build() {
    const n = sequence.next('notification');
    const tpl = faker.helpers.arrayElement(NOTIFICATION_TEMPLATES);
    return {
      id: this.data.id ?? `notif-${n}`,
      type: this.data.type ?? tpl.type,
      title: this.data.title ?? tpl.title,
      message: this.data.message ?? tpl.message,
      createdAt: this.data.createdAt ?? faker.date.recent({ days: 7 }).toISOString(),
      ...(this.data.read !== undefined ? { read: this.data.read } : {}),
    };
  }
}

NotificationFactory.TYPES = NOTIFICATION_TYPES;

export default NotificationFactory;

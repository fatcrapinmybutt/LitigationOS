/**
 * FilingFactory — Court filing and readiness test data.
 *
 * Status change: {filingId, oldStatus, newStatus}
 * Readiness update: {vehicleName, oldScore, newScore, forum}
 */
import { faker } from '@faker-js/faker';
import { sequence } from './sequence';

const FILING_STATUSES = ['drafting', 'review', 'final', 'filed', 'served'];

const VEHICLES = [
  { name: 'Emergency Application for Leave to Appeal', forum: 'MSC' },
  { name: 'Complaint for Superintending Control', forum: 'MSC' },
  { name: 'Petition for Habeas Corpus', forum: 'MSC' },
  { name: 'Writ of Mandamus', forum: 'MSC' },
  { name: 'Appeal Brief 366810', forum: 'COA' },
  { name: 'JTC Formal Complaint', forum: 'JTC' },
  { name: 'Federal §1983 Complaint', forum: 'USDC' },
  { name: 'Motion for Reconsideration', forum: '14th Circuit' },
  { name: 'Motion to Vacate Ex Parte Orders', forum: '14th Circuit' },
  { name: 'Motion to Disqualify', forum: '14th Circuit' },
  { name: 'PPO Modification', forum: '14th Circuit' },
  { name: 'Bar Complaint — Berry', forum: 'State Bar' },
];

const FORUMS = ['MSC', 'COA', 'JTC', 'USDC', '14th Circuit', 'State Bar'];

export class FilingFactory {
  constructor() {
    this.data = {};
    this.traits = [];
  }

  static statusChange(overrides) {
    return new FilingFactory().with(overrides).buildStatusChange();
  }

  static readinessUpdate(overrides) {
    return new FilingFactory().with(overrides).buildReadinessUpdate();
  }

  static createMany(count, overrides) {
    return Array.from({ length: count }, () => FilingFactory.readinessUpdate(overrides));
  }

  with(overrides) {
    if (overrides) this.data = { ...this.data, ...overrides };
    return this;
  }

  withTrait(trait) {
    this.traits.push(trait);
    return this;
  }

  /** Trait: court-ready filing (score 85+) */
  asCourtReady() {
    this.data.newScore = faker.number.int({ min: 85, max: 100 });
    this.data.newStatus = 'final';
    return this;
  }

  /** Trait: in-progress draft */
  asDraft() {
    this.data.newScore = faker.number.int({ min: 30, max: 60 });
    this.data.newStatus = 'drafting';
    return this;
  }

  /** Trait: already filed */
  asFiled() {
    this.data.oldStatus = 'final';
    this.data.newStatus = 'filed';
    this.data.newScore = 100;
    return this;
  }

  /** Trait: specific forum */
  forForum(forum) {
    this.data.forum = forum;
    return this;
  }

  buildStatusChange() {
    const n = sequence.next('filing');
    const statusIdx = faker.number.int({ min: 0, max: FILING_STATUSES.length - 2 });
    return {
      filingId: this.data.filingId ?? `filing-${n}`,
      oldStatus: this.data.oldStatus ?? FILING_STATUSES[statusIdx],
      newStatus: this.data.newStatus ?? FILING_STATUSES[statusIdx + 1],
    };
  }

  buildReadinessUpdate() {
    const vehicle = faker.helpers.arrayElement(VEHICLES);
    const oldScore = this.data.oldScore ?? faker.number.int({ min: 0, max: 80 });
    return {
      vehicleName: this.data.vehicleName ?? vehicle.name,
      oldScore,
      newScore: this.data.newScore ?? faker.number.int({ min: oldScore, max: 100 }),
      forum: this.data.forum ?? vehicle.forum,
    };
  }
}

FilingFactory.STATUSES = FILING_STATUSES;
FilingFactory.VEHICLES = VEHICLES;
FilingFactory.FORUMS = FORUMS;

export default FilingFactory;

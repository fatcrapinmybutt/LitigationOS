/**
 * ForumFactory — Case lane / forum card test data.
 *
 * For dashboard ForumCard components: {lane, label, actions, score}
 * Plus DB stats: {tables, sizeBytes, path}
 */
import { faker } from '@faker-js/faker';

const FORUM_DATA = {
  A: { label: 'Michigan Supreme Court', minActions: 4, maxActions: 15, scoreRange: [80, 100] },
  B: { label: 'Court of Appeals', minActions: 1, maxActions: 5, scoreRange: [65, 85] },
  C: { label: '14th Circuit Court', minActions: 3, maxActions: 10, scoreRange: [60, 80] },
  D: { label: 'Judicial Tenure Commission', minActions: 1, maxActions: 3, scoreRange: [85, 100] },
  E: { label: 'US District Court §1983', minActions: 3, maxActions: 8, scoreRange: [75, 95] },
  F: { label: 'State Bar of Michigan', minActions: 1, maxActions: 5, scoreRange: [70, 90] },
};

export class ForumFactory {
  constructor() {
    this.data = {};
  }

  static create(lane, overrides) {
    return new ForumFactory().forLane(lane).with(overrides).build();
  }

  /** Create all 6 forum cards */
  static createAll(overrides) {
    return Object.keys(FORUM_DATA).map((lane) => ForumFactory.create(lane, overrides));
  }

  with(overrides) {
    if (overrides) this.data = { ...this.data, ...overrides };
    return this;
  }

  forLane(lane) {
    this.data.lane = lane;
    return this;
  }

  build() {
    const lane = this.data.lane ?? faker.helpers.arrayElement(Object.keys(FORUM_DATA));
    const forum = FORUM_DATA[lane];
    return {
      lane,
      label: this.data.label ?? forum.label,
      actions: this.data.actions ?? faker.number.int({ min: forum.minActions, max: forum.maxActions }),
      score: this.data.score ?? faker.number.int({ min: forum.scoreRange[0], max: forum.scoreRange[1] }),
    };
  }
}

export class DbStatsFactory {
  constructor() {
    this.data = {};
  }

  static create(overrides) {
    return new DbStatsFactory().with(overrides).build();
  }

  with(overrides) {
    if (overrides) this.data = { ...this.data, ...overrides };
    return this;
  }

  /** Trait: large production DB */
  asProduction() {
    this.data.tables = 691;
    this.data.sizeBytes = 10_653_532_160; // ~9.92 GB
    return this;
  }

  /** Trait: empty/small test DB */
  asEmpty() {
    this.data.tables = 0;
    this.data.sizeBytes = 0;
    return this;
  }

  build() {
    return {
      tables: this.data.tables ?? faker.number.int({ min: 100, max: 700 }),
      sizeBytes: this.data.sizeBytes ?? faker.number.int({ min: 1_000_000, max: 12_000_000_000 }),
      path: this.data.path ?? 'C:\\Users\\andre\\LitigationOS\\litigation_context.db',
    };
  }
}

ForumFactory.FORUM_DATA = FORUM_DATA;

export { ForumFactory as default };

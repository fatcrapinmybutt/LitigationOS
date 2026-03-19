/**
 * EvidenceFactory — Evidence document / ingestion test data.
 *
 * Matches payload schema: {documentId, filename, type, quotesExtracted}
 * Plus batch progress: {batchId, processed, total, percent}
 */
import { faker } from '@faker-js/faker';
import { sequence } from './sequence';

const EVIDENCE_TYPES = ['pdf', 'docx', 'txt', 'md', 'jpg', 'png', 'eml', 'xlsx', 'csv'];

const EVIDENCE_FILENAMES = [
  'Court_Order_2024-001507-DC.pdf',
  'Watson_PPO_Filing_2023.pdf',
  'McNeill_Ex_Parte_Order_Aug8.pdf',
  'Berry_Voicemail_Transcript.txt',
  'Custody_Evaluation_Report.pdf',
  'Financial_Disclosure_Emily.xlsx',
  'Text_Messages_AlbertW.pdf',
  'Police_Report_Jan2024.pdf',
  'Shady_Oaks_Lease_Agreement.pdf',
  'FOC_Recommendation_2024.pdf',
  'Deposition_Transcript_Watson.pdf',
  'Email_Chain_Barnes_Court.eml',
  'Photo_Evidence_LincolnRoom.jpg',
  'Bank_Statements_Q1_2024.pdf',
  'School_Records_Lincoln.pdf',
];

const CASE_LANES = ['A', 'B', 'C', 'D', 'E', 'F'];

export class EvidenceFactory {
  constructor() {
    this.data = {};
    this.traits = [];
  }

  static create(overrides) {
    return new EvidenceFactory().with(overrides).build();
  }

  static createMany(count, overrides) {
    return Array.from({ length: count }, () => EvidenceFactory.create(overrides));
  }

  static batchProgress(overrides) {
    return new EvidenceFactory().with(overrides).buildBatchProgress();
  }

  with(overrides) {
    if (overrides) this.data = { ...this.data, ...overrides };
    return this;
  }

  withTrait(trait) {
    this.traits.push(trait);
    return this;
  }

  /** Trait: high-value evidence with many quotes */
  asHighValue() {
    this.data.quotesExtracted = faker.number.int({ min: 50, max: 500 });
    this.traits.push('high_value');
    return this;
  }

  /** Trait: court order document */
  asCourtOrder() {
    this.data.type = 'pdf';
    this.data.filename = `Court_Order_${faker.date.past().toISOString().slice(0, 10)}.pdf`;
    return this;
  }

  /** Trait: specific case lane */
  forLane(lane) {
    this.data.lane = lane;
    return this;
  }

  /** Trait: Watson-sourced evidence */
  fromWatson() {
    this.data.filename = `Watson_${faker.word.noun()}_${faker.date.past().getFullYear()}.pdf`;
    this.data.lane = 'A';
    return this;
  }

  /** Trait: judicial violation evidence */
  asJudicialViolation() {
    this.data.filename = `McNeill_Violation_${sequence.next('violation')}.pdf`;
    this.data.lane = 'E';
    return this;
  }

  build() {
    const n = sequence.next('evidence');
    return {
      documentId: this.data.documentId ?? `doc-${n}`,
      filename: this.data.filename ?? faker.helpers.arrayElement(EVIDENCE_FILENAMES),
      type: this.data.type ?? faker.helpers.arrayElement(EVIDENCE_TYPES),
      quotesExtracted: this.data.quotesExtracted ?? faker.number.int({ min: 0, max: 100 }),
      ...(this.data.lane ? { lane: this.data.lane } : {}),
    };
  }

  buildBatchProgress() {
    const n = sequence.next('batch');
    const total = this.data.total ?? faker.number.int({ min: 50, max: 5000 });
    const processed = this.data.processed ?? faker.number.int({ min: 0, max: total });
    return {
      batchId: this.data.batchId ?? `batch-${n}`,
      processed,
      total,
      percent: this.data.percent ?? (total > 0 ? Math.round((processed / total) * 100) : 0),
    };
  }
}

EvidenceFactory.TYPES = EVIDENCE_TYPES;
EvidenceFactory.LANES = CASE_LANES;

export default EvidenceFactory;

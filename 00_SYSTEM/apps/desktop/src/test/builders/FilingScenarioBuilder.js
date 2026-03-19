/**
 * FilingScenarioBuilder — Builds complex filing preparation scenarios.
 *
 * Composes filings with related evidence, deadlines, and notifications
 * to simulate realistic filing workflow sequences.
 */
import { FilingFactory } from '../factories/FilingFactory';
import { DeadlineFactory } from '../factories/DeadlineFactory';
import { EvidenceFactory } from '../factories/EvidenceFactory';
import { NotificationFactory } from '../factories/NotificationFactory';
import { faker } from '@faker-js/faker';

export class FilingScenarioBuilder {
  constructor() {
    this._forum = null;
    this._vehicleName = null;
    this._evidenceCount = 5;
    this._includeDeadline = true;
    this._includeNotifications = true;
    this._targetScore = null;
  }

  /** Set the forum (MSC, COA, JTC, USDC, 14th Circuit, State Bar) */
  forForum(forum) {
    this._forum = forum;
    return this;
  }

  /** Set the specific vehicle/filing name */
  forVehicle(vehicleName) {
    this._vehicleName = vehicleName;
    return this;
  }

  /** Set how many supporting evidence documents */
  withEvidence(count) {
    this._evidenceCount = count;
    return this;
  }

  /** Include a filing deadline */
  withDeadline(daysRemaining) {
    this._includeDeadline = true;
    this._deadlineDays = daysRemaining;
    return this;
  }

  /** Skip deadline generation */
  withoutDeadline() {
    this._includeDeadline = false;
    return this;
  }

  /** Skip notification generation */
  withoutNotifications() {
    this._includeNotifications = false;
    return this;
  }

  /** Set target readiness score */
  withTargetScore(score) {
    this._targetScore = score;
    return this;
  }

  /** Preset: MSC Emergency Application ready to file */
  asMscEmergency() {
    this._forum = 'MSC';
    this._vehicleName = 'Emergency Application for Leave to Appeal';
    this._targetScore = 95;
    this._deadlineDays = 3;
    this._evidenceCount = 20;
    return this;
  }

  /** Preset: COA brief in progress */
  asCoaBrief() {
    this._forum = 'COA';
    this._vehicleName = 'Appeal Brief 366810';
    this._targetScore = 75;
    this._deadlineDays = 14;
    this._evidenceCount = 15;
    return this;
  }

  /** Preset: JTC complaint ready */
  asJtcComplaint() {
    this._forum = 'JTC';
    this._vehicleName = 'JTC Formal Complaint';
    this._targetScore = 92;
    this._deadlineDays = 30;
    this._evidenceCount = 25;
    return this;
  }

  /**
   * Build the complete filing scenario.
   * @returns {{ filing, evidence, deadline, notifications, readinessHistory }}
   */
  build() {
    const forum = this._forum ?? faker.helpers.arrayElement(FilingFactory.FORUMS);
    const vehicle = this._vehicleName ??
      FilingFactory.VEHICLES.find((v) => v.forum === forum)?.name ??
      'Generic Filing';
    const targetScore = this._targetScore ?? faker.number.int({ min: 60, max: 100 });

    // Filing readiness — progressive score increases
    const readinessHistory = [];
    let score = 0;
    const steps = faker.number.int({ min: 3, max: 8 });
    for (let i = 0; i < steps; i++) {
      const oldScore = score;
      score = Math.min(targetScore, score + Math.ceil(targetScore / steps) + faker.number.int({ min: -5, max: 5 }));
      readinessHistory.push({
        vehicleName: vehicle,
        oldScore: oldScore,
        newScore: Math.min(score, 100),
        forum,
      });
    }

    // Current filing status
    const filing = FilingFactory.statusChange({
      oldStatus: targetScore >= 85 ? 'review' : 'drafting',
      newStatus: targetScore >= 85 ? 'final' : 'review',
    });

    // Supporting evidence
    const evidence = EvidenceFactory.createMany(this._evidenceCount);

    // Deadline
    const deadline = this._includeDeadline
      ? DeadlineFactory.create({
          title: `${vehicle} Due`,
          daysRemaining: this._deadlineDays ?? faker.number.int({ min: 5, max: 30 }),
        })
      : null;

    // Notifications
    const notifications = this._includeNotifications
      ? [
          NotificationFactory.create({
            type: 'filing',
            title: 'Filing Score Updated',
            message: `${vehicle} scored ${targetScore}/100`,
          }),
          ...(targetScore >= 85
            ? [NotificationFactory.create({
                type: 'success',
                title: 'Filing Ready',
                message: `${vehicle} is court-ready`,
              })]
            : []),
        ]
      : [];

    return {
      filing,
      forum,
      vehicleName: vehicle,
      targetScore,
      evidence,
      deadline,
      notifications,
      readinessHistory,
    };
  }
}

export default FilingScenarioBuilder;

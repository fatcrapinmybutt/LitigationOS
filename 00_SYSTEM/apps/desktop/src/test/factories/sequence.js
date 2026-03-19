/**
 * Sequence generator for deterministic test IDs.
 *
 * Provides auto-incrementing counters keyed by name.
 * Reset between tests via sequence.reset().
 */
class Sequence {
  constructor() {
    /** @type {Map<string, number>} */
    this.counters = new Map();
  }

  /**
   * Get the next integer in the named sequence.
   * @param {string} key
   * @returns {number}
   */
  next(key) {
    const current = this.counters.get(key) || 0;
    const next = current + 1;
    this.counters.set(key, next);
    return next;
  }

  /**
   * Peek at the current value without incrementing.
   * @param {string} key
   * @returns {number}
   */
  current(key) {
    return this.counters.get(key) || 0;
  }

  /**
   * Reset a single sequence or all sequences.
   * @param {string} [key] - If omitted, resets all.
   */
  reset(key) {
    if (key) {
      this.counters.delete(key);
    } else {
      this.counters.clear();
    }
  }
}

export const sequence = new Sequence();
export default sequence;

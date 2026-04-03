/**
 * API client — wraps all calls to the FastAPI backend.
 * Change BASE_URL here if the backend port changes.
 */

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api';

// Sentinel error type so callers can detect "run no longer exists on server"
export class RunExpiredError extends Error {
  constructor() { super('Run expired — server was restarted. Please start a new run.'); }
}

async function request(method, path, body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) opts.body = JSON.stringify(body);

  const res = await fetch(`${BASE_URL}${path}`, opts);
  if (!res.ok) {
    if (res.status === 404 && path.includes('/rpg/')) throw new RunExpiredError();
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

export const api = {
  /** Start a new game. Returns full game state including session_id. */
  newGame: () => request('POST', '/game/new'),

  /** Get current game state. */
  getState: (sessionId) => request('GET', `/game/${sessionId}/state`),

  /** Select a number to collect on this roll. */
  selectNumber: (sessionId, number) =>
    request('POST', `/game/${sessionId}/select`, { number }),

  /** Skip turn when no dice can form any valid combination. */
  skipTurn: (sessionId) => request('POST', `/game/${sessionId}/skip`),

  /** Get AI's ranked list of legal moves for coaching display. */
  getAiHint: (sessionId) => request('GET', `/game/${sessionId}/ai-hint`),
};

// ---------------------------------------------------------------------------
// RPG API
// ---------------------------------------------------------------------------

export const rpgApi = {
  /** Start a new RPG run. */
  newRun: () => request('POST', '/rpg/new'),

  /** Get full run state. */
  getState: (runId) => request('GET', `/rpg/${runId}/state`),

  /** Select a number during upgrade phase. */
  upgradeSelect: (runId, number) =>
    request('POST', `/rpg/${runId}/upgrade/select`, { number }),

  /** Skip turn during upgrade phase (no valid combos). */
  upgradeSkip: (runId) => request('POST', `/rpg/${runId}/upgrade/skip`),

  /** Free reroll — re-rolls all dice without costing a turn (requires forge). */
  upgradeReroll: (runId) => request('POST', `/rpg/${runId}/upgrade/reroll`),

  /** Retry die reroll — rerolls only the retry die without costing a turn (once per turn). */
  upgradeRetryReroll: (runId) => request('POST', `/rpg/${runId}/upgrade/retry-reroll`),

  /** Apply upgrades and move to combat phase. */
  upgradeFinish: (runId) => request('POST', `/rpg/${runId}/upgrade/finish`),

  /** Simulate the fight and get combat events. */
  startCombat: (runId) => request('POST', `/rpg/${runId}/combat/start`),

  /** Buy an item in the shop. Pass useFree=true to spend a free item pick. */
  buyItem: (runId, itemId, useFree = false) =>
    request('POST', `/rpg/${runId}/shop/buy`, { item_id: itemId, use_free: useFree }),

  /** Spend 30g to refresh the shop items. */
  rerollShop: (runId) => request('POST', `/rpg/${runId}/shop/reroll`),

  /** Leave the shop and proceed to next level. */
  closeShop: (runId) => request('POST', `/rpg/${runId}/shop/close`),

  /** Pick a pre-game forge specialisation before the first enemy. */
  preGameForgePick: (runId, choiceId) =>
    request('POST', `/rpg/${runId}/pre_game_forge/pick`, { choice_id: choiceId }),

  /** Pick a forge upgrade after defeating a boss. */
  forgePick: (runId, choiceId) =>
    request('POST', `/rpg/${runId}/forge/pick`, { choice_id: choiceId }),

  /** Fetch full run history. */
  getHistory: () => request('GET', '/rpg/history'),

  /** Wipe all run history. */
  clearHistory: () => request('DELETE', '/rpg/history'),
};

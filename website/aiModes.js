// aiModes.js
// LocalStorage-first intelligent modes with gamification hooks.

const STORAGE_KEY = "daisy_ai_mode_v1";

const defaultState = {
  aiMode: "Motivator",
  tasksCompleted: 0,
  pomodorosCompleted: 0,
};

const getState = () => {
  const raw = localStorage.getItem(STORAGE_KEY);
  return raw ? JSON.parse(raw) : { ...defaultState };
};

const setState = (next) => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
};

const setMode = (mode) => {
  const state = getState();
  state.aiMode = mode;
  setState(state);
};

const getMode = () => getState().aiMode;

// Short, upbeat responses per mode
const modeResponses = {
  Motivator: [
    "You’re on fire. Keep stacking wins.",
    "Nice momentum. One more focused sprint.",
    "You’re building a streak. Let’s go.",
  ],
  Coach: [
    "Try the 1‑3‑5 rule: 1 big, 3 medium, 5 small tasks.",
    "Start with the hardest task for 25 minutes, then reassess.",
    "Break it down into a 5‑minute entry step.",
  ],
  Companion: [
    "I’m here. Let’s make today feel lighter.",
    "Tell me what’s on your mind, I’ll help.",
    "You’re doing great. We can go one step at a time.",
  ],
  RewardMaster: [
    "Big win! Confetti unlocked.",
    "That’s the dopamine hit. Enjoy it.",
    "Legendary focus. Coins incoming.",
  ],
  SilentFocus: [
    "Ready when you are.",
    "Listening.",
    "Standing by.",
  ],
};

const randomPick = (arr) => arr[Math.floor(Math.random() * arr.length)];

// Reward policies per mode
const rewardRules = {
  Motivator: {
    taskBonus: 3,
    pomodoroBonus: 5,
    randomBonusChance: 0.0,
  },
  Coach: {
    taskBonus: 0,
    pomodoroBonus: 0,
    randomBonusChance: 0.0,
  },
  Companion: {
    taskBonus: 0,
    pomodoroBonus: 0,
    randomBonusChance: 0.1,
  },
  RewardMaster: {
    taskBonus: 5,
    pomodoroBonus: 8,
    randomBonusChance: 0.1,
  },
  SilentFocus: {
    taskBonus: 0,
    pomodoroBonus: 0,
    randomBonusChance: 0.0,
  },
};

const shouldRandomBonus = (chance) => Math.random() < chance;

// Hook helpers: pass in DaisyAPI + Dopamine from your app
const applyModeReward = async ({ baseCoins, reason, DaisyAPI, Dopamine, onReward }) => {
  const mode = getMode();
  const rules = rewardRules[mode] || rewardRules.Motivator;
  let bonus = 0;

  if (reason === "task") bonus += rules.taskBonus;
  if (reason === "pomodoro") bonus += rules.pomodoroBonus;

  if (shouldRandomBonus(rules.randomBonusChance)) {
    bonus += 5;
    Dopamine?.sparkleBurst?.(window.innerWidth / 2, window.innerHeight * 0.6, 18);
  }

  const total = baseCoins + bonus;

  if (total > 0 && DaisyAPI?.earnCoins) {
    const res = await DaisyAPI.earnCoins({ amount: total, reason: `mode_${reason}` });
    onReward?.(res?.reward?.total ?? total, res?.reward?.bonus ?? 0);
    if (mode === "RewardMaster") {
      Dopamine?.sparkleBurst?.(window.innerWidth / 2, window.innerHeight * 0.6, 24);
      Dopamine?.playSound?.("sounds/unlock.mp3");
    }
    return res;
  }
  return null;
};

// AI response generator (local simulation, optional LLM hook later)
const generateResponse = (mode, context = {}) => {
  if (mode === "SilentFocus" && !context.prompted) return "";
  let base = randomPick(modeResponses[mode] || modeResponses.Motivator);

  if (mode === "Motivator" && context.streak) {
    base += ` Streak: ${context.streak} days.`;
  }
  if (mode === "Companion" && context.coins) {
    base += ` You’ve got ${context.coins} coins.`;
  }
  return base;
};

export const AIModes = {
  getMode,
  setMode,
  getState,
  setState,
  generateResponse,
  applyModeReward,
};

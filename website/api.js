/* Daisy API helper (local-first mock for website-only mode) */
(() => {
  const STATE_KEY = "daisy_state_v2";

  function todayStr() {
    const d = new Date();
    return d.toISOString().slice(0, 10);
  }

  function defaultQuests(date) {
    return {
      date,
      items: [
        { id: "quest_focus", label: "Complete a focus session", done: false },
        { id: "quest_task", label: "Finish one task", done: false },
        { id: "quest_chat", label: "Ask Daisy for advice", done: false },
      ],
      bonus_awarded: false,
    };
  }

  function loadState() {
    const raw = localStorage.getItem(STATE_KEY);
    if (raw) return JSON.parse(raw);
    const date = todayStr();
    const state = {
      coins: 0,
      unlimited_coins: false,
      streak: 0,
      last_active_date: null,
      coins_today: 0,
      focus_minutes_today: 0,
      unlocks: {
        pastel: false,
        glow: false,
        confetti: false,
        avatar: false,
      },
      quests: defaultQuests(date),
      history: {
        tasks: [],
        pomodoros: [],
      },
    };
    localStorage.setItem(STATE_KEY, JSON.stringify(state));
    return state;
  }

  function saveState(state) {
    localStorage.setItem(STATE_KEY, JSON.stringify(state));
  }

  function applyStreak(state, activityDate) {
    if (!state.last_active_date) {
      state.streak = 1;
      state.last_active_date = activityDate;
      return 0;
    }
    if (state.last_active_date === activityDate) {
      return 0;
    }
    const last = new Date(state.last_active_date);
    const current = new Date(activityDate);
    const diffDays = Math.round((current - last) / (1000 * 60 * 60 * 24));
    if (diffDays === 1) {
      state.streak += 1;
      state.last_active_date = activityDate;
      return 20;
    }
    state.streak = 1;
    state.last_active_date = activityDate;
    return 0;
  }

  function maybeResetDaily(state) {
    const date = todayStr();
    if (state.quests.date !== date) {
      state.quests = defaultQuests(date);
      state.coins_today = 0;
      state.focus_minutes_today = 0;
    }
  }

  function awardCoins(state, amount, reason) {
    const date = todayStr();
    maybeResetDaily(state);
    const streakBonus = applyStreak(state, date);
    let bonus = 0;
    if (Math.random() < 0.1) {
      bonus = 5;
    }
    const total = amount + streakBonus + bonus;
    state.coins += total;
    state.coins_today += total;
    return { total, bonus, streakBonus };
  }

  function levelFromCoins(coins) {
    return Math.floor(coins / 100);
  }

  function balancePayload(state) {
    const level = levelFromCoins(state.coins);
    return {
      coins: state.coins,
      streak: state.streak,
      last_active_date: state.last_active_date,
      level,
      level_progress: state.coins % 100,
      next_level_at: (level + 1) * 100,
      theme_unlocked: state.unlocks.pastel,
      coins_today: state.coins_today,
      focus_minutes_today: state.focus_minutes_today,
      quests: state.quests,
      unlocks: state.unlocks,
    };
  }

  const DaisyAPI = {
    getBalance: async () => {
      const state = loadState();
      maybeResetDaily(state);
      saveState(state);
      return balancePayload(state);
    },
    completeTask: async () => {
      const state = loadState();
      const reward = awardCoins(state, 5, "task_completed");
      state.history.tasks.unshift({
        type: "task_completed",
        coins: 5,
        timestamp: new Date().toISOString(),
      });
      state.quests.items.find((q) => q.id === "quest_task").done = true;
      saveState(state);
      return { ...balancePayload(state), reward };
    },
    completePomodoro: async ({ duration_minutes }) => {
      const state = loadState();
      const coins = duration_minutes >= 25 ? 10 : 0;
      const reward = coins ? awardCoins(state, coins, "pomodoro") : { total: 0, bonus: 0, streakBonus: 0 };
      state.focus_minutes_today += duration_minutes;
      state.history.pomodoros.unshift({
        duration: duration_minutes,
        coins,
        completed_at: new Date().toISOString(),
      });
      if (duration_minutes >= 25) {
        state.quests.items.find((q) => q.id === "quest_focus").done = true;
      }
      saveState(state);
      return { ...balancePayload(state), reward };
    },
    spendCoins: async ({ amount, reason }) => {
      const state = loadState();
      if (state.unlimited_coins) {
        if (reason === "theme_unlock") state.unlocks.pastel = true;
        if (reason === "glow_unlock") state.unlocks.glow = true;
        if (reason === "confetti_unlock") state.unlocks.confetti = true;
        if (reason === "avatar_unlock") state.unlocks.avatar = true;
        saveState(state);
        return balancePayload(state);
      }
      if (state.coins < amount) throw new Error("Insufficient coins");
      state.coins -= amount;
      if (reason === "theme_unlock") state.unlocks.pastel = true;
      if (reason === "glow_unlock") state.unlocks.glow = true;
      if (reason === "confetti_unlock") state.unlocks.confetti = true;
      if (reason === "avatar_unlock") state.unlocks.avatar = true;
      saveState(state);
      return balancePayload(state);
    },
    aiChat: async ({ message }) => {
      const state = loadState();
      if (state.coins < 1) throw new Error("Not enough coins for AI chat");
      state.coins -= 1;
      state.quests.items.find((q) => q.id === "quest_chat").done = true;
      saveState(state);
      const replies = [
        "Nice focus energy. You're building real momentum today.",
        "Great ask. Small steps now = big wins later. Keep the streak alive.",
        "You're doing better than you think. One more task and you're golden.",
        "Love the consistency. Coins and clarity are stacking.",
      ];
      const reply = replies[Math.floor(Math.random() * replies.length)];
      return { reply };
    },
    history: async () => {
      const state = loadState();
      return {
        tasks: state.history.tasks,
        pomodoros: state.history.pomodoros,
      };
    },
    dailyQuestStatus: async () => {
      const state = loadState();
      maybeResetDaily(state);
      saveState(state);
      return state.quests;
    },
    setQuestDone: async (questId, done) => {
      const state = loadState();
      const q = state.quests.items.find((item) => item.id === questId);
      if (q) q.done = done;
      saveState(state);
      return state.quests;
    },
    completeDailyQuests: async () => {
      const state = loadState();
      const allDone = state.quests.items.every((q) => q.done);
      if (allDone && !state.quests.bonus_awarded) {
        const reward = awardCoins(state, 20, "daily_quest");
        state.quests.bonus_awarded = true;
        saveState(state);
        return { ...balancePayload(state), reward, daily_bonus: true };
      }
      saveState(state);
      return { ...balancePayload(state), daily_bonus: false };
    },
    waitlist: async ({ email }) => {
      const key = "daisy_waitlist";
      const list = JSON.parse(localStorage.getItem(key) || "[]");
      if (!list.includes(email)) list.push(email);
      localStorage.setItem(key, JSON.stringify(list));
      return { status: "ok", email };
    },
    unlockAll: async () => {
      const state = loadState();
      state.unlocks = {
        pastel: true,
        glow: true,
        confetti: true,
        avatar: true,
      };
      saveState(state);
      return balancePayload(state);
    },
    enableUnlimitedCoins: async () => {
      const state = loadState();
      state.unlimited_coins = true;
      state.coins = Math.max(state.coins, 999999);
      saveState(state);
      return balancePayload(state);
    },
  };

  window.DaisyAPI = DaisyAPI;
})();

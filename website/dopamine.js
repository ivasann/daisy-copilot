// dopamine.js
export const Dopamine = (() => {
  const colors = ["#FFD700", "#FFB6C1", "#87CEFA", "#90EE90", "#FF69B4"];

  // Play sound helper (silent fallback if missing)
  const playSound = (src) => {
    try {
      const audio = new Audio(src);
      audio.volume = 0.2;
      audio.play().catch(() => {});
    } catch (_) {
      // ignore if audio fails
    }
  };

  // Floating coins animation
  const floatCoins = (x, y, text = "+10") => {
    const coin = document.createElement("div");
    coin.innerText = text;
    coin.style.position = "fixed";
    coin.style.left = `${x}px`;
    coin.style.top = `${y}px`;
    coin.style.fontWeight = "bold";
    coin.style.fontSize = "20px";
    coin.style.color = colors[Math.floor(Math.random() * colors.length)];
    coin.style.zIndex = 9999;
    coin.style.transition = "all 1s ease-out";
    coin.style.opacity = 1;
    document.body.appendChild(coin);

    requestAnimationFrame(() => {
      coin.style.transform = "translateY(-50px) scale(1.5)";
      coin.style.opacity = 0;
    });

    setTimeout(() => coin.remove(), 1000);
    playSound("sounds/coin.mp3");
  };

  // Sparkle particle burst
  const sparkleBurst = (x, y, count = 10) => {
    for (let i = 0; i < count; i += 1) {
      const star = document.createElement("div");
      star.style.position = "fixed";
      star.style.left = `${x}px`;
      star.style.top = `${y}px`;
      star.style.width = "6px";
      star.style.height = "6px";
      star.style.background = colors[Math.floor(Math.random() * colors.length)];
      star.style.borderRadius = "50%";
      star.style.opacity = 1;
      star.style.transition = "all 1s ease-out";
      document.body.appendChild(star);

      const dx = (Math.random() - 0.5) * 100;
      const dy = (Math.random() - 0.5) * 100;

      requestAnimationFrame(() => {
        star.style.transform = `translate(${dx}px, ${dy}px) scale(0.5)`;
        star.style.opacity = 0;
      });

      setTimeout(() => star.remove(), 1000);
    }
  };

  // Pomodoro celebration overlay
  const pomodoroCelebration = () => {
    const overlay = document.createElement("div");
    overlay.style.position = "fixed";
    overlay.style.left = "0";
    overlay.style.top = "0";
    overlay.style.width = "100%";
    overlay.style.height = "100%";
    overlay.style.background = "rgba(255,255,255,0.3)";
    overlay.style.zIndex = 9998;
    overlay.style.display = "flex";
    overlay.style.justifyContent = "center";
    overlay.style.alignItems = "center";
    overlay.style.fontSize = "40px";
    overlay.style.color = "#FFD700";
    overlay.style.fontWeight = "bold";
    overlay.innerText = "🎉 Pomodoro Complete! +10 Coins!";
    document.body.appendChild(overlay);
    sparkleBurst(window.innerWidth / 2, window.innerHeight / 2, 20);
    playSound("sounds/pomodoro.mp3");
    setTimeout(() => overlay.remove(), 1500);
  };

  // Shop unlock animation
  const shopUnlock = (itemName = "Theme") => {
    const popup = document.createElement("div");
    popup.innerText = `✨ ${itemName} Unlocked! ✨`;
    popup.style.position = "fixed";
    popup.style.left = "50%";
    popup.style.top = "20%";
    popup.style.transform = "translateX(-50%)";
    popup.style.padding = "15px 25px";
    popup.style.background = "#fff";
    popup.style.borderRadius = "1rem";
    popup.style.boxShadow = "0 0 20px rgba(0,0,0,0.2)";
    popup.style.fontSize = "24px";
    popup.style.zIndex = 9999;
    document.body.appendChild(popup);
    sparkleBurst(window.innerWidth / 2, window.innerHeight / 2, 30);
    playSound("sounds/unlock.mp3");
    setTimeout(() => popup.remove(), 2000);
  };

  // Streak warning pulse
  const streakWarning = (element) => {
    if (!element) return;
    element.style.transition = "all 0.5s ease-in-out";
    element.style.transform = "scale(1.2)";
    element.style.color = "#FF4500";
    setTimeout(() => {
      element.style.transform = "scale(1)";
      element.style.color = "#FFD700";
    }, 500);
  };

  return {
    floatCoins,
    sparkleBurst,
    pomodoroCelebration,
    shopUnlock,
    streakWarning,
    playSound,
  };
})();

document.addEventListener("DOMContentLoaded", () => {
    const RTP = parseFloat(document.body.dataset.rtp || "0.97");
    const MAX_CHANCE = 0.95;

    let selectedSource = "balance";
    let selectedInventoryId = null;
    let selectedItemPrice = null;
    let selectedMultiplier = 2;

    const balanceInput = document.getElementById("balance-amount");
    const chanceDisplay = document.getElementById("chance-display");
    const targetDisplay = document.getElementById("target-display");
    const upgradeBtn = document.getElementById("upgrade-btn");
    const dialArc = document.getElementById("dial-arc");
    const dialPointer = document.getElementById("dial-pointer");
    const rdChance = document.getElementById("rd-chance");
    const rdStatus = document.getElementById("rd-status");
    const resultMessage = document.getElementById("result-message");
    const userBalanceLabel = document.getElementById("user-balance");

    let currentRotation = 0; // накопленный угол, чтобы стрелка всегда крутилась вперёд

    // --- Табы источника ставки ---
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
            btn.classList.add("active");
            document.getElementById(btn.dataset.tab).classList.add("active");

            selectedSource = btn.dataset.tab === "balance-tab" ? "balance" : "item";
            recalc();
        });
    });

    // --- Выбор предмета ---
    document.querySelectorAll(".mini-skin-card").forEach(card => {
        card.addEventListener("click", () => {
            document.querySelectorAll(".mini-skin-card").forEach(c => c.classList.remove("selected"));
            card.classList.add("selected");
            selectedInventoryId = card.dataset.inventoryId;
            selectedItemPrice = parseFloat(card.dataset.price);
            recalc();
        });
    });

    if (balanceInput) {
        balanceInput.addEventListener("input", recalc);
    }

    // --- Выбор множителя ---
    document.querySelectorAll(".mult-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".mult-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            selectedMultiplier = parseFloat(btn.dataset.mult);
            recalc();
        });
    });

    function getStakeValue() {
        if (selectedSource === "balance") {
            return parseFloat(balanceInput.value) || 0;
        }
        return selectedItemPrice || 0;
    }

    function recalc() {
        const stake = getStakeValue();
        let chance = (1 / selectedMultiplier) * RTP;
        chance = Math.max(0.01, Math.min(chance, MAX_CHANCE));
        const target = Math.round(stake * selectedMultiplier);

        chanceDisplay.textContent = (chance * 100).toFixed(1) + "%";
        targetDisplay.textContent = target + " 💰";

        paintDial(chance * 100);
    }

    function paintDial(chancePct) {
        dialArc.style.background =
            `conic-gradient(from 0deg, var(--toxic) 0%, var(--toxic) ${chancePct}%, var(--blood) ${chancePct}%, var(--blood) 100%)`;
        rdChance.innerHTML = chancePct.toFixed(1) + "<span>%</span>";
    }

    recalc();

    // --- Дебаг-кнопки форс-результата (только если сервер разрешил и юзер админ) ---
    const forceWinBtn = document.getElementById("force-win-btn");
    const forceLoseBtn = document.getElementById("force-lose-btn");
    if (forceWinBtn) forceWinBtn.addEventListener("click", () => runUpgrade(true));
    if (forceLoseBtn) forceLoseBtn.addEventListener("click", () => runUpgrade(false));

    upgradeBtn.addEventListener("click", () => runUpgrade(null));

    async function runUpgrade(forceResult) {
        const stake = getStakeValue();

        if (selectedSource === "item" && !selectedInventoryId) {
            alert("Выбери предмет для ставки.");
            return;
        }
        if (selectedSource === "balance" && stake <= 0) {
            alert("Введи сумму ставки.");
            return;
        }

        upgradeBtn.disabled = true;
        resultMessage.textContent = "";
        resultMessage.className = "result-message";
        rdStatus.textContent = "Крутим…";
        rdStatus.className = "rd-status";

        const payload = {
            source: selectedSource,
            multiplier: selectedMultiplier,
        };
        if (selectedSource === "balance") {
            payload.amount = stake;
        } else {
            payload.inventory_id = selectedInventoryId;
        }
        if (forceResult !== null) {
            payload.force_result = forceResult;
        }

        try {
            const res = await fetch("/api/upgrade", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            const data = await res.json();

            if (!res.ok) {
                alert(data.error || "Ошибка апгрейда");
                upgradeBtn.disabled = false;
                rdStatus.textContent = "Готов к запуску";
                return;
            }

            // Перекрашиваем прибор под реальный шанс с сервера (на случай расхождений округления)
            paintDial(data.chance);

            // Крутим стрелку: несколько полных оборотов + финальный угол по roll
            const extraSpins = 4 + Math.floor(Math.random() * 2); // 4-5 оборотов для эффекта
            currentRotation += extraSpins * 360 + (data.roll * 3.6);
            requestAnimationFrame(() => {
                dialPointer.style.transform = `translateX(-50%) rotate(${currentRotation}deg)`;
            });

            setTimeout(() => {
                if (data.win) {
                    resultMessage.textContent = data.result_skin
                        ? `Победа! Получен: ${data.result_skin.full_name}`
                        : "Победа!";
                    resultMessage.classList.add("win");
                    rdStatus.textContent = "Победа";
                    rdStatus.className = "rd-status win";
                } else {
                    resultMessage.textContent = "Не повезло. Ставка сгорела.";
                    resultMessage.classList.add("lose");
                    rdStatus.textContent = "Проигрыш";
                    rdStatus.className = "rd-status lose";
                }
                if (userBalanceLabel) {
                    userBalanceLabel.textContent = data.new_balance;
                    userBalanceLabel.parentElement.classList.remove("balance-flash");
                    void userBalanceLabel.parentElement.offsetWidth;
                    userBalanceLabel.parentElement.classList.add("balance-flash");
                }
                upgradeBtn.disabled = false;

                // Обновляем страницу через паузу, чтобы подтянуть инвентарь и историю
                setTimeout(() => window.location.reload(), 1600);
            }, 3100);

        } catch (err) {
            console.error(err);
            alert("Не удалось выполнить апгрейд.");
            upgradeBtn.disabled = false;
            rdStatus.textContent = "Готов к запуску";
        }
    }
});

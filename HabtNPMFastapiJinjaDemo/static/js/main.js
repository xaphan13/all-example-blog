// Небольшой пример клиентской логики: дёргаем JSON API и показываем ответ.
document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("ping-btn");
    const result = document.getElementById("ping-result");
    if (!button || !result) return;

    button.addEventListener("click", async () => {
        result.textContent = "Запрос...";
        try {
            const response = await fetch("/api/ping");
            const data = await response.json();
            result.textContent = `Ответ: ${data.status} — ${data.message}`;
        } catch (error) {
            result.textContent = "Ошибка запроса";
        }
    });
});

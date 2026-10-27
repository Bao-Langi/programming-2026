const form = document.getElementById("quiz");
const result = document.getElementById("result");

form.addEventListener("submit", (event) => {
    event.preventDefault();

    const cards = document.querySelectorAll(".card");
    let score = 0;

    cards.forEach((card) => {
        const checked = card.querySelector("input:checked");
        const options = card.querySelectorAll(".option");

        // сбросить подсветку от прошлой проверки
        options.forEach((opt) => opt.classList.remove("correct", "wrong"));

        // подсветить правильный вариант
        const correctOption = options[Number(card.dataset.answer)];
        correctOption.classList.add("correct");

        // посчитать балл и подсветить ошибку
        if (checked && checked.value === card.dataset.answer) {
            score++;
        } else if (checked) {
            checked.closest(".option").classList.add("wrong");
        }
    });

    result.textContent = `Score: ${score} / ${cards.length}`;
    form.querySelectorAll("input").forEach((input) => {
        input.disabled = true;
    });
    form.querySelector("button").disabled = true;
});
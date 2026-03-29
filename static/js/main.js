function askGlobalAI() {
    let question = document.getElementById("global-question").value;

    fetch("/ask-ai", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: `question=${encodeURIComponent(question)}`
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById("global-answer").innerText = data.answer;
    });
}

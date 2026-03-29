function askAI() {
    let question = document.getElementById("question").value;

    fetch("/ask-ai", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: `question=${encodeURIComponent(question)}`
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById("answer").innerText = data.answer;
    });
}

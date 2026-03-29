function askGlobalAI() {
    let question = document.getElementById("global-question").value;

    fetch("/ask-ai", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ question: question })
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById("global-answer").innerText = data.answer;
    })
    .catch(err => {
        console.error(err);
        document.getElementById("global-answer").innerText = "Error connecting AI";
    });
}

const BACKEND_URL = "https://edu-platform-sqty.onrender.com";
const TOKEN = localStorage.getItem("token");

async function loadDashboardData() {
    try {
        const res = await fetch(`${BACKEND_URL}/admin/stats`, {
            headers: { "Authorization": `Bearer ${TOKEN}` }
        });
        const data = await res.json();
        
        // Safety checks to prevent "not defined" errors
        if(document.getElementById('totalUsers')) document.getElementById('totalUsers').innerText = data.total_users || 0;
        if(document.getElementById('totalRevenue')) document.getElementById('totalRevenue').innerText = `₹${data.total_revenue || 0}`;
        if(document.getElementById('userNameDisplay')) document.getElementById('userNameDisplay').innerText = localStorage.getItem("userName") || "Harman";
    } catch(e) {
        console.log("Stats fetch failed - user might not be approved yet.");
    }
}

async function askAI() {
    const question = document.getElementById('aiQuestion').value;
    const responseBox = document.getElementById('aiResponse');
    
    responseBox.classList.remove('hidden');
    responseBox.innerText = "Processing query...";

    try {
        const res = await fetch(`${BACKEND_URL}/ai/solve-doubt`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${TOKEN}` },
            body: JSON.stringify({ 
                question: question,
                image_url: null // Later we can add actual image uploading
            })
        });
        const data = await res.json();
        responseBox.innerHTML = `<b>AI Answer:</b><br>${data.answer}`;
    } catch(e) {
        responseBox.innerText = "Error: Backend is sleeping or not responding.";
    }
}

function showPayment() { document.getElementById('paymentModal').classList.remove('hidden'); }
function hidePayment() { document.getElementById('paymentModal').classList.add('hidden'); }

// Function to handle section switching
function showSection(name) {
    alert("Loading " + name + " System... (Accessing Database)");
    // This will fetch from the /batches or /institutes routes we built in app.py
}

window.onload = loadDashboardData;

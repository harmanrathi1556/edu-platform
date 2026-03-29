const BACKEND_URL = "https://edu-platform-sqty.onrender.com";
const USER_TOKEN = localStorage.getItem("token") || "GUEST_TOKEN"; // Placeholder until login is fully connected

// --- FEATURE #19: LOAD REAL-TIME STATS ---
async function loadDashboardData() {
    try {
        const response = await fetch(`${BACKEND_URL}/admin/stats`, {
            headers: { "Authorization": USER_TOKEN }
        });
        const stats = await response.json();
        
        if (stats.total_users !== undefined) {
            document.getElementById('totalRevenue').innerText = `₹${stats.total_revenue}`;
            document.getElementById('totalUsers').innerText = stats.total_users;
            document.getElementById('userXP').innerText = `${stats.total_users * 50} XP`; // Demo logic
        }
    } catch (err) {
        console.log("Stats update failed - waiting for real login token.");
    }
}

// --- FEATURE #14: AI DOUBT SOLVER ---
async function askAI() {
    const question = document.getElementById('aiQuestion').value;
    const responseBox = document.getElementById('aiResponse');
    
    if(!question) return alert("Please type your doubt first!");
    
    responseBox.innerHTML = "✨ <span class='animate-pulse'>AI is analyzing your query...</span>";
    responseBox.classList.remove('hidden');

    try {
        const res = await fetch(`${BACKEND_URL}/ai/solve-doubt`, {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "Authorization": USER_TOKEN
            },
            body: JSON.stringify({ question: question })
        });
        const data = await res.json();
        responseBox.innerHTML = `<strong>Answer:</strong><br>${data.answer}`;
    } catch (err) {
        responseBox.innerText = "Error connecting to AI Brain. Check Render logs.";
    }
}

// --- FEATURE #7: PAYMENT MODAL CONTROLS ---
function showPayment() {
    document.getElementById('paymentModal').classList.remove('hidden');
}

function hidePayment() {
    document.getElementById('paymentModal').classList.add('hidden');
}

async function submitPayment() {
    const btn = document.getElementById('paySubmitBtn');
    const amount = document.getElementById('payAmount').value;
    const screenshot = document.getElementById('qrUrl').value;
    const batch = document.getElementById('selectedBatch').value;
    const coupon = document.getElementById('couponCode').value;

    if(!amount || !screenshot) return alert("Please fill all payment details!");

    btn.innerText = "Uploading...";

    try {
        const res = await fetch(`${BACKEND_URL}/payment/submit`, {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "Authorization": USER_TOKEN
            },
            body: JSON.stringify({ 
                amount: amount, 
                screenshot_url: screenshot, 
                batch_id: batch,
                coupon_code: coupon
            })
        });
        
        const data = await res.json();
        alert("Payment Recorded! " + data.message);
        hidePayment();
    } catch (err) {
        alert("Submission failed. Check your internet.");
    } finally {
        btn.innerText = "Submit Payment";
    }
}

// Auto-run on load
window.onload = loadDashboardData;

let currentSection = 0;
const sections = document.querySelectorAll(".form-section");
const progressBar = document.getElementById("progressBar");

function updateProgressBar() {
    const percent = ((currentSection + 1) / sections.length) * 100;
    progressBar.style.width = percent + "%";
}
function previousSection() {
    if (currentSection > 0) {
        sections[currentSection].classList.remove("active");
        currentSection--;
        sections[currentSection].classList.add("active");
        updateProgressBar();
    }
}



function nextSection() {
    const inputs = sections[currentSection].querySelectorAll("input, select");
    let valid = true;

    inputs.forEach(input => {
        if ((input.type === "text" || input.type === "number") && input.value.trim() === "") {
            input.style.border = "2px solid red";
            valid = false;
        } else if (input.tagName === "SELECT" && input.value === "") {
            input.style.border = "2px solid red";
            valid = false;
        } else {
            input.style.border = "";
        }
    });

    if (!valid) {
        alert("Please fill all fields before proceeding.");
        return;
    }

    if (currentSection < sections.length - 1) {
        sections[currentSection].classList.remove("active");
        currentSection++;
        sections[currentSection].classList.add("active");
        updateProgressBar();
    }
}

document.getElementById("leprosyForm").addEventListener("submit", async function (e) {
    e.preventDefault();

    const inputs = sections[currentSection].querySelectorAll("input, select");
    let valid = true;

    inputs.forEach(input => {
        if ((input.type === "text" || input.type === "number") && input.value.trim() === "") {
            input.style.border = "2px solid red";
            valid = false;
        } else if (input.tagName === "SELECT" && input.value === "") {
            input.style.border = "2px solid red";
            valid = false;
        } else {
            input.style.border = "";
        }
    });

    if (!valid) {
        alert("Please fill all fields before submitting.");
        return;
    }

    const formData = new FormData(this);
    const data = {};
    formData.forEach((val, key) => data[key] = val);

    try {
        const res = await fetch("/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        if (!res.ok) {
            throw new Error("Server error while predicting.");
        }

        const result = await res.json();

        document.getElementById("result").innerHTML = `
            <h3>Prediction Results</h3>
            <p><strong>Classification:</strong> ${result.Output_Classification}</p>
            <p><strong>Treatment:</strong> ${result.Output_Treatment}</p>
            <p><strong>Reaction Type:</strong> ${result.Output_ReactionType}</p>
            <p><strong>Reaction Treatment:</strong> ${result.Output_ReactionTreatment}</p>
        `;
    } catch (error) {
        console.error("Prediction error:", error);
        alert("An error occurred during prediction. Please try again.");
    }
});

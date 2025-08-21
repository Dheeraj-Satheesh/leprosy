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

        // Display prediction results
        document.getElementById("result").innerHTML = `
            <h3>Prediction Results</h3>
            <p><strong>Leprosy Diagnosis:</strong> ${result.Output_Classification}</p>
            <p><strong>Leprosy Treatment:</strong> ${result.Output_Treatment}</p>
              <p><strong>Max (WHO) Disability Grade:</strong> ${result.Max_Disability_Grade}</p>
            <p><strong>Lepra Reaction Identification:</strong> ${result.Output_ReactionType}</p>
            <p><strong>Lepra Reaction Treatment:</strong> ${result.Output_ReactionTreatment}</p>
        `;

        // Show download button
        const downloadBtn = document.getElementById("downloadReport");
        downloadBtn.style.display = "inline-block";

        // Bind click for PDF download
        downloadBtn.onclick = function () {
            const { jsPDF } = window.jspdf;
            const doc = new jsPDF();

            // Colors
            const primaryColor = [255, 94, 98];
            const sectionBg = [245, 245, 245];

            // Patient info
            let patientName = document.querySelector('input[name="name"]')?.value || "N/A";
            let gender = document.querySelector('select[name="Gender"]')?.value || "N/A";
            let age = document.querySelector('input[name="Age"]')?.value || "N/A";
            let weight = document.querySelector('input[name="Weight"]')?.value || "N/A";

            // Observations (Yes only)
            let observations = [];
            document.querySelectorAll("select, input").forEach(input => {
                if (input.value && input.value.toLowerCase() === "yes") {
                    let label = input.closest("label")
                        ? input.closest("label").innerText
                        : input.name;
                    observations.push(label.trim());
                }
            });
            if (observations.length === 0) {
                observations.push("No positive observations reported.");
            }

            // === HEADER ===
            doc.setFontSize(20);
            doc.setTextColor(...primaryColor);
            doc.text("Leprosy Prediction Summary", 105, 15, null, null, "center");
            doc.setDrawColor(...primaryColor);
            doc.line(20, 18, 190, 18);

            // === DATE ===
            doc.setFontSize(11);
            doc.setTextColor(0, 0, 0);
            doc.text(`Date: ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}`, 20, 25);

            // === PATIENT INFO BOX ===
            doc.setFillColor(227, 242, 253); // Soft light blue
            doc.rect(20, 30, 170, 25, "F");
            doc.setFontSize(12);
            doc.setFont(undefined, "bold");
            doc.text("Patient Information", 22, 36);
            doc.setFont(undefined, "normal");
            doc.text(`Name: ${patientName}`, 22, 42);
            doc.text(`Sex: ${gender}`, 90, 42);
            doc.text(`Age: ${age}`, 22, 48);
            doc.text(`Weight: ${weight}`, 90, 48);

            // === OBSERVATIONS BOX ===
            let obsY = 62;
            doc.setFillColor(232, 245, 233); // Pale green
            doc.rect(20, obsY - 6, 170, (observations.length * 6) + 10, "F");
            doc.setFont(undefined, "bold");
            doc.text("Observations", 22, obsY);
            doc.setFont(undefined, "normal");
            obsY += 6;
            observations.forEach(obs => {
                doc.text(`• ${obs}`, 25, obsY);
                obsY += 6;
            });

            // === PREDICTION OUTPUT BOX ===
            // === PREDICTION OUTPUT BOX ===
            obsY += 6;
            doc.setFillColor(255, 243, 224); // Light peach
            doc.rect(20, obsY - 6, 170, 50, "F");   // height +10 to fit extra line
            doc.setFont(undefined, "bold");
            doc.text("Prediction Output", 22, obsY);
            doc.setFont(undefined, "normal");
            doc.text(`Leprosy Diagnosis: ${result.Output_Classification}`, 22, obsY + 8);
            doc.text(`Leprosy Treatment: ${result.Output_Treatment}`, 22, obsY + 14);
            doc.text(`Max (WHO) Disability Grade: ${result.Max_Disability_Grade}`, 22, obsY + 20);
            doc.text(`Lepra Reaction Identification: ${result.Output_ReactionType}`, 22, obsY + 26);
            doc.text(`Lepra Reaction Treatment: ${result.Output_ReactionTreatment}`, 22, obsY + 32);

            // === FOOTER NOTE ===
            doc.setFontSize(9);
            doc.setTextColor(50, 50, 50); // Dark grey
            doc.setFont(undefined, "bold");
            doc.text(
                'Note: "The leprosy prediction tool provides an assessment based on the clinical data you input. It is crucial to use this report as an aid and to base the final treatment decisions on your own clinical judgment, considering the patient\'s physical examination, condition, and medical history. Additionally, always follow the national guidelines for leprosy treatment."',
                20, 280, { maxWidth: 170 }
            );


            // Save PDF
            doc.save(`Leprosy_Report_${patientName}.pdf`);
        };

    } catch (error) {
        console.error("Prediction error:", error);
        alert("An error occurred during prediction. Please try again.");
    }
});

// Welcome screen fade-out
document.addEventListener("DOMContentLoaded", function () {
    const welcome = document.getElementById("welcome-screen");
    if (welcome) {
        setTimeout(() => {
            welcome.classList.add("fade-out");
            setTimeout(() => {
                welcome.remove();
            }, 1000);
        }, 5000);
    }
});

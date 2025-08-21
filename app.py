from flask import Flask, request, jsonify, render_template
import joblib
from datetime import datetime
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

# Load the sklearn model and label encoders
model = joblib.load("model_rf.pkl")
label_encoders = {
    'Output_Classification': joblib.load('enc_classification.pkl'),
    'Output_Treatment': joblib.load('enc_treatment.pkl'),
    'Output_ReactionType': joblib.load('enc_reactiontype.pkl'),
    'Output_ReactionTreatment': joblib.load('enc_reactiontreatment.pkl')
}

# Feature order expected by the model
feature_order = [
    "Age",
    "Loss of eyebrows Full/partial",
    "Nasal infiltration (Saddle Nose Deformity)",
    "Thickening of ear lobes",
    "Blink absent less than 6 months(corneal reflex)",
    "Blink absent more than 6 months(corneal reflex)",
    "Inability to close eyes less than 6 months(Lagophthalmos)",
    "Inability to close eyes more than 6 months(Lagophthalmos)",
    "Changes in the skin color( Hypo pigmentation) with partial or complete loss of sensation",
    "Changes in the skin color(Erythematous) with partial or complete loss of sensation",
    "Changes in the skin color( Hypo pigmentation) with  sensation",
    "Changes in the skin color(Erythematous) with  sensation",
    "Thickend skin on the patches",
    "Shiny or oily skin",
    "Nodules on skin",
    "Skin Lesions- Raised, Redness, Warmth,Painful (Hypo/Erythema)",
    "Nodules-Painful swellings under the skin",
    "Painful Skin Lesions/Nodules",
    "Loss of sensation in the Palm(S)",
    "Weakness in hand(s) when grasping or holding objects",
    "Inability to feel cold or hot objects",
    "Ulnar claw - Little & Ring fingers claw less than 6 months",
    "Ulnar claw - Little & Ring fingers claw more than 6 months",
    "Median Claw - Middle, Index, Thumb fingers claw less than 6 months",
    "Median Claw - Middle, Index, Thumb fingers claw more than 6 months",
    "Radial sensory loss (affecting the lateral 3 ½ digits, and associated with the area on the dorsum of the hand)",
    "Wrist Drop- Unable to do wrist up less than 6 months",
    "Wrist Drop- Unable to do wrist up more than 6 months",
    "Painless wounds or burns on palms",
    "Lateral Popliteal Nerve sensory loss-lower leg over the posterolateral part of the leg and the knee joint",
    "Foot Drop -Unable to do foot up / Weakness / Dragging the foot while walking less than 6 months",
    "Foot Drop- Unable to do foot up / Weakness / Dragging the foot while walking for more than 6 months",
    "Loss of sensation in sole of foot/feet",
    "Ulceration in foot /feet; painless wounds or burns on foot/feet",
    "Clawing (toes )",
    "Number of skin lessions/Nodules less than 5",
    "Number of skin lesions /Nodules greater than 5",
    "Never treated MDT",
    "Irregular Treatment MDT",
    "Completed Treatment MDT",
    "Existing skin lesion /Nodules increasing in size, sudden onset",
    "Existing skin lesion /Nodules increasing in size, slow onset",
    "Appearing New Skin lesions/ Nodules suddenly",
    "Existing skin lesion /Nodules  not increasing size /anaesthesia remains same"
]


@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    input_features = []
    record = {}

    # Include name and age
    record["Patient_Name"] = data.get("name", "")
    record["Age"] = data.get("Age", "")

    # Collect model input features
    for key in feature_order:
        val = data.get(key, "No")
        if isinstance(val, str) and val.lower() == "yes":
            input_features.append(1)
        elif isinstance(val, str) and val.lower() == "no":
            input_features.append(0)
        else:
            input_features.append(float(val))
        record[key] = val

    # Get prediction from model
    pred = model.predict([input_features])[0]
    result = {
        'Output_Classification': label_encoders['Output_Classification'].inverse_transform([pred[0]])[0],
        'Output_Treatment': label_encoders['Output_Treatment'].inverse_transform([pred[1]])[0],
        'Output_ReactionType': label_encoders['Output_ReactionType'].inverse_transform([pred[2]])[0],
        'Output_ReactionTreatment': label_encoders['Output_ReactionTreatment'].inverse_transform([pred[3]])[0],
    }
     # 🔹 Disability Grade Calculation
    grade_map = { "0": "Gr-0", "1": "Gr-I", "2": "Gr-II" }
    eye = data.get("Disability_Grade_Eyes", "")
    hand = data.get("Disability_Grade_Hands", "")
    foot = data.get("Disability_Grade_Feet", "")

    disability_grades = [eye, hand, foot]
    disability_grades = [int(g) for g in disability_grades if g != ""]
    max_grade = max(disability_grades) if disability_grades else None

    result['Max_Disability_Grade'] = grade_map[str(max_grade)] if max_grade is not None else "N/A"

    # Add result and timestamp
    record.update(result)
    record['Timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Send to Google Sheets
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        google_creds_dict = json.loads(os.environ["GOOGLE_CREDS_JSON"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open("Leprosy Submissions").sheet1

        # If new sheet, insert header
        if sheet.row_count < 2:
            header = ["Patient_Name"] + feature_order + list(result.keys()) + ["Timestamp"]
            sheet.insert_row(header, index=1)

        row = [record["Patient_Name"]] + [record.get(k, "") for k in feature_order] + \
              [result['Output_Classification'], result['Output_Treatment'],
               result['Output_ReactionType'], result['Output_ReactionTreatment'],
               record['Timestamp']]

        sheet.append_row(row)

    except Exception as e:
        print("Google Sheets logging failed:", e)

    return jsonify(result)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)

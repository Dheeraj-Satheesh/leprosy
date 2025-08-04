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
    "Age", "loss_eyebrow", "nasal", "ear_lobes",
    "blink_lt6", "blink_gt6", "eye_close_lt6", "eye_close_gt6",
    "Any changes in the skin color( Hypo pigmentation) with partial or complete loss of sensation",
    "Any changes in the skin color(Erythematous) with partial or complete loss of sensation",
    "Any changes in the skin color( Hypo pigmentation) with  sensation",
    "Any changes in the skin color(Erythematous) with  sensation",
    "Thickend skin on the patches", "Shiny or oily skin", "Nodules on skin",
    "Painful Skin Lesions", "Painful Nodules", "Itching Skin lesion/Nodules",
    "palm_sensation", "weak_grip", "temp_sense_hand", "ulnar_lt6", "ulnar_gt6",
    "median_lt6", "median_gt6", "radial_sensory", "wrist_up_lt6", "wrist_up_gt6", "burns_palm",
    "lateral_popliteal",
    "Unable to do foot up (foot drop) /Weakness/Dragging the foot while walking less than 6 months",
    "Unable to do foot up(foot drop) /Weakness/Dragging the foot while walking for more than 6 months",
    "Loss of sensation in sole of foot/feet",
    "Ulceration in foot /feet; painless wounds or burns on foot/feet",
    "Clawing (toes )",
    "Number of skin lessions/Nodules less than 5",
    "Number of skin lesions /Nodules greater than 5", "Not treated MDT",
    "Irregular Treatment MDT", "Completed Treatment MDT",
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

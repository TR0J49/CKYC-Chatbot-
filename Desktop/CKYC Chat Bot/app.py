from flask import Flask, render_template, request, jsonify, session
import uuid
from database import init_db, log_session, log_query, log_api_query, log_feedback, get_report
from faqs import get_faq_answer
from translations import t

app = Flask(__name__)
app.secret_key = "ckyc-chatbot-secret-key-2026"


@app.before_request
def ensure_session():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
        session["wrong_count"] = 0
        session["language"] = "en"
        session["user_type"] = None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/admin")
def admin():
    return render_template("admin.html")


@app.route("/api/set-language", methods=["POST"])
def set_language():
    data = request.json
    lang = data.get("language", "en")
    session["language"] = lang
    session["wrong_count"] = 0
    return jsonify({"status": "ok", "language": lang})


@app.route("/api/set-user-type", methods=["POST"])
def set_user_type():
    data = request.json
    user_type = data.get("user_type", "client")
    session["user_type"] = user_type
    log_session(session["session_id"], session["language"], user_type)
    return jsonify({"status": "ok", "user_type": user_type})


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "").strip()
    lang = session.get("language", "en")

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    result = get_faq_answer(user_message, lang)

    if result["is_greeting"]:
        response = t("hello_response", lang)
        log_query(session["session_id"], user_message, response, "Greeting", None, 1)
        session["wrong_count"] = 0
        return jsonify({
            "response": response,
            "matched": True,
            "show_redirect": False,
        })

    if result["matched"]:
        response = result["answer"]
        log_query(session["session_id"], user_message, response, result["category"], result["faq_id"], 1)
        session["wrong_count"] = 0
        return jsonify({
            "response": response,
            "matched": True,
            "show_redirect": False,
        })

    # Not matched - increment wrong count
    wrong_count = session.get("wrong_count", 0) + 1
    session["wrong_count"] = wrong_count

    if wrong_count >= 3:
        response = t("redirect_msg", lang)
        log_query(session["session_id"], user_message, response, None, None, 0)
        session["wrong_count"] = 0
        return jsonify({
            "response": response,
            "matched": False,
            "show_redirect": True,
        })
    else:
        response = t("not_understood", lang)
        log_query(session["session_id"], user_message, response, None, None, 0)
        return jsonify({
            "response": response,
            "matched": False,
            "show_redirect": False,
        })


@app.route("/api/check-status", methods=["POST"])
def check_status():
    data = request.json
    reg_number = data.get("reg_number", "").strip()
    lang = session.get("language", "en")

    if not reg_number:
        return jsonify({"error": "Registration number is required"}), 400

    # Simulated status check (in production, this would call actual CKYC API)
    statuses = {
        "en": [
            f"Registration/Acknowledgment Number: {reg_number}\nStatus: Under Processing\nSubmitted on: 2026-01-15\nExpected completion: 3-5 working days",
            f"Registration/Acknowledgment Number: {reg_number}\nStatus: Accepted\nCKYC Number has been generated successfully.",
            f"Registration/Acknowledgment Number: {reg_number}\nStatus: Pending Verification\nYour documents are under review.",
        ],
        "hi": [
            f"पंजीकरण/पावती संख्या: {reg_number}\nस्थिति: प्रसंस्करण के अंतर्गत\nजमा करने की तिथि: 2026-01-15\nअपेक्षित पूर्णता: 3-5 कार्य दिवस",
            f"पंजीकरण/पावती संख्या: {reg_number}\nस्थिति: स्वीकृत\nCKYC नंबर सफलतापूर्वक जनरेट हो गया है।",
            f"पंजीकरण/पावती संख्या: {reg_number}\nस्थिति: सत्यापन लंबित\nआपके दस्तावेज़ समीक्षाधीन हैं।",
        ],
    }

    import random
    status_response = random.choice(statuses.get(lang, statuses["en"]))
    log_api_query(session["session_id"], "status_check", reg_number, status_response)

    return jsonify({"response": status_response})


@app.route("/api/wallet-inquiry", methods=["POST"])
def wallet_inquiry():
    data = request.json
    re_number = data.get("re_number", "").strip()
    option = data.get("option", 1)
    lang = session.get("language", "en")

    if not re_number:
        return jsonify({"error": "RE registration number is required"}), 400

    # Simulated wallet data
    wallet_data = {
        1: {
            "en": f"RE Number: {re_number}\nAvailable Balance: ₹15,250.75\nLast Transaction: 2026-02-05",
            "hi": f"RE नंबर: {re_number}\nउपलब्ध शेष: ₹15,250.75\nअंतिम लेनदेन: 2026-02-05",
        },
        2: {
            "en": f"RE Number: {re_number}\nTDS on Hold: ₹1,525.08\nFinancial Year: 2025-26",
            "hi": f"RE नंबर: {re_number}\nहोल्ड पर TDS: ₹1,525.08\nवित्तीय वर्ष: 2025-26",
        },
        3: {
            "en": f"RE Number: {re_number}\nThreshold Limit: ₹50,000.00\nCurrent Usage: ₹34,749.25",
            "hi": f"RE नंबर: {re_number}\nसीमा सीमा: ₹50,000.00\nवर्तमान उपयोग: ₹34,749.25",
        },
        4: {
            "en": f"RE Number: {re_number}\nMinimum Balance Limit: ₹5,000.00\nCurrent Balance: ₹15,250.75",
            "hi": f"RE नंबर: {re_number}\nन्यूनतम शेष सीमा: ₹5,000.00\nवर्तमान शेष: ₹15,250.75",
        },
    }

    response = wallet_data.get(int(option), wallet_data[1])
    response_text = response.get(lang, response["en"])
    log_api_query(session["session_id"], f"wallet_inquiry_{option}", re_number, response_text)

    return jsonify({"response": response_text})


@app.route("/api/mismatch-check", methods=["POST"])
def mismatch_check():
    data = request.json
    ckyc_number = data.get("ckyc_number", "").strip()
    lang = session.get("language", "en")

    if not ckyc_number:
        return jsonify({"error": "CKYC number is required"}), 400

    if len(ckyc_number) != 14 or not ckyc_number.isdigit():
        error_msg = {
            "en": "Please enter a valid 14-digit CKYC number.",
            "hi": "कृपया एक मान्य 14-अंकीय CKYC नंबर दर्ज करें।",
        }
        return jsonify({"error": error_msg.get(lang, error_msg["en"])}), 400

    # Simulated response
    response = {
        "en": f"CKYC Number: {ckyc_number}\nRegistered Financial Institution: State Bank of India\nLast Updated: 2026-01-20\nStatus: Active\n\nIf you find any mismatch, please contact your Financial Institution to initiate the correction process.",
        "hi": f"CKYC नंबर: {ckyc_number}\nपंजीकृत वित्तीय संस्थान: भारतीय स्टेट बैंक\nअंतिम अपडेट: 2026-01-20\nस्थिति: सक्रिय\n\nयदि आपको कोई बेमेल मिलता है, तो कृपया सुधार प्रक्रिया शुरू करने के लिए अपने वित्तीय संस्थान से संपर्क करें।",
    }

    response_text = response.get(lang, response["en"])
    log_api_query(session["session_id"], "mismatch_check", ckyc_number, response_text)

    return jsonify({"response": response_text})


@app.route("/api/feedback", methods=["POST"])
def submit_feedback():
    data = request.json
    rating = data.get("rating", "")
    rating_value = data.get("rating_value", 3)
    feedback_text = data.get("feedback_text", "")
    lang = session.get("language", "en")

    log_feedback(session["session_id"], rating, rating_value, feedback_text)

    if rating_value <= 2:
        response = t("feedback_bad", lang)
    else:
        response = t("feedback_good", lang)

    return jsonify({"response": response})


@app.route("/api/end-chat", methods=["POST"])
def end_chat():
    lang = session.get("language", "en")
    response = t("thank_you", lang)
    # Reset session counters
    session["wrong_count"] = 0
    return jsonify({"response": response})


@app.route("/api/reset", methods=["POST"])
def reset_session():
    session["session_id"] = str(uuid.uuid4())
    session["wrong_count"] = 0
    session["language"] = "en"
    session["user_type"] = None
    return jsonify({"status": "ok"})


@app.route("/api/report", methods=["GET"])
def report():
    report_type = request.args.get("type", "today")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    data = get_report(report_type, start_date, end_date)
    return jsonify(data)


@app.route("/api/translations", methods=["GET"])
def get_translations():
    lang = request.args.get("lang", "en")
    from translations import TRANSLATIONS
    result = {}
    for key, val in TRANSLATIONS.items():
        result[key] = val.get(lang, val.get("en", key))
    return jsonify(result)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)

"""
FAQ data and NLP-based matching engine for CKYC chatbot.
Uses TF-IDF + Cosine Similarity for intelligent question matching.
"""

import re
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# ====== NLP SETUP ======
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words("english"))
# Keep important CKYC terms even if they're stop words
KEEP_WORDS = {"what", "how", "who", "when", "where", "why", "not", "no"}
stop_words -= KEEP_WORDS


def preprocess(text):
    """Clean, tokenize, remove stopwords, and lemmatize text."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)  # remove punctuation
    text = re.sub(r"\s+", " ", text)  # normalize whitespace
    tokens = word_tokenize(text)
    tokens = [lemmatizer.lemmatize(t) for t in tokens if t not in stop_words and len(t) > 1]
    return " ".join(tokens)


# ====== FAQ DATA ======
FAQS = [
    {
        "id": "faq_1",
        "category": "General",
        "keywords": ["what", "ckyc", "central kyc", "registry", "about"],
        "question": {
            "en": "What is Central KYC Registry?",
            "hi": "सेंट्रल केवाईसी रजिस्ट्री क्या है?",
        },
        "answer": {
            "en": "Central KYC Registry is a centralized repository of KYC records of customers in the financial sector with uniform KYC norms and inter-usability of the KYC records across the sector with an objective to reduce the burden of producing KYC documents and getting those verified every time when the customer creates a new relationship with a financial entity.",
            "hi": "सेंट्रल केवाईसी रजिस्ट्री वित्तीय क्षेत्र में ग्राहकों के केवाईसी रिकॉर्ड का एक केंद्रीकृत भंडार है जिसमें एकसमान केवाईसी मानदंड और क्षेत्र भर में केवाईसी रिकॉर्ड की अंतर-उपयोगिता है, जिसका उद्देश्य ग्राहक द्वारा किसी वित्तीय संस्था के साथ नया संबंध बनाने पर हर बार केवाईसी दस्तावेज प्रस्तुत करने और उनका सत्यापन कराने के बोझ को कम करना है।",
        },
        "training_phrases": [
            "what is central kyc registry",
            "what is ckyc",
            "tell me about ckyc",
            "what does ckyc mean",
            "explain central kyc",
            "about ckyc registry",
            "ckyc kya hai",
            "what is ckycrr",
            "central kyc records registry",
            "what is kyc registry",
            "define ckyc",
        ],
    },
    {
        "id": "faq_2",
        "category": "General",
        "keywords": ["who", "set up", "setup", "established", "created", "manage"],
        "question": {
            "en": "Who has set up the Central KYC Records Registry?",
            "hi": "सेंट्रल केवाईसी रिकॉर्ड्स रजिस्ट्री किसने स्थापित की है?",
        },
        "answer": {
            "en": "The Central Registry of Securitisation Asset Reconstruction and Security Interest of India (CERSAI) has been appointed by the Government of India to act as, and to perform the functions of the Central KYC Records Registry under the Prevention of Money Laundering (Maintenance of Records) Rules, 2005.",
            "hi": "भारत सरकार द्वारा सेंट्रल रजिस्ट्री ऑफ सिक्यूरिटाइजेशन एसेट रिकंस्ट्रक्शन एंड सिक्योरिटी इंटरेस्ट ऑफ इंडिया (CERSAI) को धन शोधन निवारण (रिकॉर्ड का रखरखाव) नियम, 2005 के तहत सेंट्रल केवाईसी रिकॉर्ड्स रजिस्ट्री के रूप में कार्य करने और इसके कार्यों को करने के लिए नियुक्त किया गया है।",
        },
        "training_phrases": [
            "who set up ckyc",
            "who created ckyc registry",
            "who manages ckyc",
            "who established central kyc",
            "ckyc setup by whom",
            "who runs ckyc",
            "what is cersai",
            "who is behind ckyc",
            "government ckyc",
        ],
    },
    {
        "id": "faq_3",
        "category": "CKYC Number",
        "keywords": ["digits", "digit", "how many", "number", "ckyc number", "14"],
        "question": {
            "en": "How many digits is the CKYC number?",
            "hi": "CKYC नंबर कितने अंकों का होता है?",
        },
        "answer": {
            "en": "The CKYC number is a 14-digit unique identification number issued to every individual whose KYC details are registered in the Central KYC Records Registry (CKYCRR).",
            "hi": "CKYC नंबर एक 14-अंकीय विशिष्ट पहचान संख्या है जो प्रत्येक व्यक्ति को जारी की जाती है जिसका केवाईसी विवरण सेंट्रल केवाईसी रिकॉर्ड्स रजिस्ट्री (CKYCRR) में पंजीकृत है।",
        },
        "training_phrases": [
            "how many digits ckyc number",
            "ckyc number digits",
            "how long is ckyc number",
            "length of ckyc number",
            "14 digit ckyc",
            "ckyc number format",
            "what is ckyc number",
            "ckyc number kya hota hai",
            "ckyc identification number",
        ],
    },
    {
        "id": "faq_4",
        "category": "Registration",
        "keywords": ["register", "registration", "how to register", "enroll", "signup", "upload"],
        "question": {
            "en": "How to register on CKYC?",
            "hi": "CKYC पर पंजीकरण कैसे करें?",
        },
        "answer": {
            "en": "KYC records are uploaded by the Financial Institutions (reporting entities) with whom you have a relationship. You need to submit your KYC documents to your Financial Institution (Bank, Insurance Company, Mutual Fund, etc.), and they will upload your KYC data to the Central KYC Registry.",
            "hi": "केवाईसी रिकॉर्ड वित्तीय संस्थानों (रिपोर्टिंग संस्थाओं) द्वारा अपलोड किए जाते हैं जिनके साथ आपका संबंध है। आपको अपने वित्तीय संस्थान (बैंक, बीमा कंपनी, म्यूचुअल फंड, आदि) में अपने केवाईसी दस्तावेज जमा करने होंगे, और वे आपका केवाईसी डेटा सेंट्रल केवाईसी रजिस्ट्री में अपलोड करेंगे।",
        },
        "training_phrases": [
            "how to register on ckyc",
            "ckyc registration process",
            "how to do ckyc",
            "register for ckyc",
            "enroll in ckyc",
            "sign up for central kyc",
            "how to get ckyc done",
            "ckyc kaise kare",
            "upload kyc records",
            "how does kyc get uploaded",
        ],
    },
    {
        "id": "faq_5",
        "category": "Charges",
        "keywords": ["charges", "cost", "fee", "fees", "price", "rate", "download", "verification", "amount", "payment"],
        "question": {
            "en": "What are the verification/download charges?",
            "hi": "सत्यापन/डाउनलोड शुल्क क्या हैं?",
        },
        "answer": {
            "en": "The rates applicable for Downloads are as under:\n1. First time download of KYC record - Rupees 2.25 per record\n2. Subsequent download of KYC record by the same reporting entity - Re 1.00 per record\n\nNote:\ni. The download charges shall be debited from the wallet of the reporting entity.\nii. The charge is exclusive of any applicable relevant tax.",
            "hi": "डाउनलोड के लिए लागू दरें इस प्रकार हैं:\n1. केवाईसी रिकॉर्ड की पहली बार डाउनलोड - ₹2.25 प्रति रिकॉर्ड\n2. उसी रिपोर्टिंग संस्था द्वारा केवाईसी रिकॉर्ड की बाद की डाउनलोड - ₹1.00 प्रति रिकॉर्ड\n\nनोट:\ni. डाउनलोड शुल्क रिपोर्टिंग संस्था के वॉलेट से डेबिट किया जाएगा।\nii. शुल्क किसी भी लागू प्रासंगिक कर से अतिरिक्त है।",
        },
        "training_phrases": [
            "what are the charges",
            "download charges",
            "verification charges",
            "how much does it cost",
            "ckyc fees",
            "rate for download",
            "price of kyc record",
            "cost of ckyc download",
            "what is the fee",
            "charges for kyc verification",
            "download fee",
            "kitna charge lagta hai",
        ],
    },
    {
        "id": "faq_6",
        "category": "Documents",
        "keywords": ["documents", "document", "required", "kyc documents", "proof", "identity", "address"],
        "question": {
            "en": "What documents are required for KYC?",
            "hi": "केवाईसी के लिए कौन से दस्तावेज आवश्यक हैं?",
        },
        "answer": {
            "en": "The following documents are generally required for KYC:\n1. Proof of Identity: Aadhaar Card, PAN Card, Passport, Voter ID, Driving License\n2. Proof of Address: Aadhaar Card, Passport, Utility Bills, Bank Statement\n3. Recent passport-size photograph\n\nNote: The specific requirements may vary depending on the type of financial institution.",
            "hi": "केवाईसी के लिए आमतौर पर निम्नलिखित दस्तावेज आवश्यक होते हैं:\n1. पहचान प्रमाण: आधार कार्ड, पैन कार्ड, पासपोर्ट, मतदाता पहचान पत्र, ड्राइविंग लाइसेंस\n2. पता प्रमाण: आधार कार्ड, पासपोर्ट, उपयोगिता बिल, बैंक स्टेटमेंट\n3. हालिया पासपोर्ट आकार का फोटो\n\nनोट: विशिष्ट आवश्यकताएं वित्तीय संस्थान के प्रकार के अनुसार भिन्न हो सकती हैं।",
        },
        "training_phrases": [
            "what documents are required",
            "kyc documents needed",
            "documents for ckyc",
            "what id proof is needed",
            "identity proof for kyc",
            "address proof for kyc",
            "which documents for kyc",
            "list of kyc documents",
            "aadhaar pan for ckyc",
            "document list for ckyc registration",
        ],
    },
    {
        "id": "faq_7",
        "category": "CKYC Number",
        "keywords": ["find", "check", "know", "get", "obtain", "my ckyc", "ckyc number", "search"],
        "question": {
            "en": "How to find/check my CKYC number?",
            "hi": "अपना CKYC नंबर कैसे खोजें/जांचें?",
        },
        "answer": {
            "en": "You can find your CKYC number by:\n1. Checking with your bank or financial institution where you completed KYC.\n2. Visiting the CKYC portal (https://www.ckycindia.in) and searching using your PAN or other identification details.\n3. Your CKYC number may be mentioned in communications from your financial institution.",
            "hi": "आप अपना CKYC नंबर इस प्रकार पा सकते हैं:\n1. अपने बैंक या वित्तीय संस्थान से जांच करें जहां आपने केवाईसी पूरा किया।\n2. CKYC पोर्टल (https://www.ckycindia.in) पर जाएं और अपने पैन या अन्य पहचान विवरण का उपयोग करके खोजें।\n3. आपका CKYC नंबर आपके वित्तीय संस्थान से प्राप्त संचार में उल्लिखित हो सकता है।",
        },
        "training_phrases": [
            "how to find my ckyc number",
            "check ckyc number",
            "where to get ckyc number",
            "how to know my ckyc number",
            "search ckyc number",
            "find ckyc number using pan",
            "how to obtain ckyc number",
            "ckyc number kaise pata kare",
            "retrieve ckyc number",
            "i want my ckyc number",
        ],
    },
    {
        "id": "faq_8",
        "category": "Update",
        "keywords": ["update", "change", "modify", "edit", "correction", "amend", "amendment"],
        "question": {
            "en": "How to update CKYC details?",
            "hi": "CKYC विवरण कैसे अपडेट करें?",
        },
        "answer": {
            "en": "To update your CKYC details:\n1. Visit your bank or financial institution.\n2. Submit an updated KYC form along with the supporting documents for the changes.\n3. The financial institution will upload the updated details to the Central KYC Registry.\n\nNote: Direct updates by individuals are not allowed. All updates must be routed through a registered financial institution.",
            "hi": "अपना CKYC विवरण अपडेट करने के लिए:\n1. अपने बैंक या वित्तीय संस्थान पर जाएं।\n2. परिवर्तनों के लिए सहायक दस्तावेजों के साथ एक अद्यतन केवाईसी फॉर्म जमा करें।\n3. वित्तीय संस्थान अद्यतन विवरण सेंट्रल केवाईसी रजिस्ट्री में अपलोड करेगा।\n\nनोट: व्यक्तियों द्वारा सीधे अपडेट की अनुमति नहीं है। सभी अपडेट एक पंजीकृत वित्तीय संस्थान के माध्यम से किए जाने चाहिए।",
        },
        "training_phrases": [
            "how to update ckyc details",
            "change ckyc information",
            "modify kyc data",
            "correct my ckyc details",
            "edit ckyc record",
            "amendment in ckyc",
            "update name in ckyc",
            "change address in ckyc",
            "ckyc me change kaise kare",
            "update my kyc",
        ],
    },
    {
        "id": "faq_9",
        "category": "General",
        "keywords": ["benefits", "advantage", "why", "purpose", "benefit", "important"],
        "question": {
            "en": "What are the benefits of Central KYC?",
            "hi": "सेंट्रल केवाईसी के क्या लाभ हैं?",
        },
        "answer": {
            "en": "Benefits of Central KYC include:\n1. One-time KYC process - customers need not undergo KYC process every time they establish a new relationship with a financial entity.\n2. Uniform KYC norms across all financial institutions.\n3. Inter-usability of KYC records across the financial sector.\n4. Reduced documentation burden on customers.\n5. Faster on-boarding with financial institutions.\n6. Centralized and secure storage of KYC records.",
            "hi": "सेंट्रल केवाईसी के लाभ:\n1. एक बार की केवाईसी प्रक्रिया - ग्राहकों को हर बार वित्तीय संस्था के साथ नया संबंध स्थापित करने पर केवाईसी प्रक्रिया से नहीं गुजरना पड़ता।\n2. सभी वित्तीय संस्थानों में एकसमान केवाईसी मानदंड।\n3. वित्तीय क्षेत्र में केवाईसी रिकॉर्ड की अंतर-उपयोगिता।\n4. ग्राहकों पर दस्तावेज़ीकरण का बोझ कम।\n5. वित्तीय संस्थानों के साथ तेज़ ऑन-बोर्डिंग।\n6. केवाईसी रिकॉर्ड का केंद्रीकृत और सुरक्षित भंडारण।",
        },
        "training_phrases": [
            "benefits of ckyc",
            "why is ckyc important",
            "advantage of central kyc",
            "purpose of ckyc",
            "what is the use of ckyc",
            "why do we need ckyc",
            "ckyc ke fayde",
            "importance of ckyc",
        ],
    },
    {
        "id": "faq_10",
        "category": "Wallet",
        "keywords": ["wallet", "balance", "recharge", "fund", "funds", "add money", "top up"],
        "question": {
            "en": "How to recharge/add funds to the wallet?",
            "hi": "वॉलेट में रिचार्ज/फंड कैसे जोड़ें?",
        },
        "answer": {
            "en": "Registered Entities can recharge their wallet by:\n1. Logging into the CKYC portal.\n2. Navigating to the Wallet section.\n3. Selecting the recharge option.\n4. Making payment through available payment methods (NEFT/RTGS/Online).\n\nNote: Minimum balance must be maintained in the wallet for uninterrupted services.",
            "hi": "पंजीकृत संस्थाएं अपने वॉलेट को इस प्रकार रिचार्ज कर सकती हैं:\n1. CKYC पोर्टल में लॉगिन करें।\n2. वॉलेट सेक्शन पर जाएं।\n3. रिचार्ज विकल्प चुनें।\n4. उपलब्ध भुगतान विधियों (NEFT/RTGS/ऑनलाइन) के माध्यम से भुगतान करें।\n\nनोट: निर्बाध सेवाओं के लिए वॉलेट में न्यूनतम शेष राशि बनाए रखनी होगी।",
        },
        "training_phrases": [
            "how to recharge wallet",
            "add funds to wallet",
            "wallet recharge",
            "add money to ckyc wallet",
            "top up wallet",
            "wallet balance",
            "fund wallet",
            "how to add balance",
            "wallet me paise kaise dale",
        ],
    },
    {
        "id": "faq_11",
        "category": "Status",
        "keywords": ["status", "track", "tracking", "application", "pending", "progress", "acknowledgment"],
        "question": {
            "en": "How to check the status of CKYC application?",
            "hi": "CKYC आवेदन की स्थिति कैसे जांचें?",
        },
        "answer": {
            "en": "You can check the status of your CKYC application by:\n1. Using the 'Check Status' option in this chatbot and entering your FI registration/acknowledgment number.\n2. Visiting the CKYC portal (https://www.ckycindia.in).\n3. Contacting your financial institution.\n\nThe status can be: Submitted, Under Processing, Accepted, or Rejected.",
            "hi": "आप अपने CKYC आवेदन की स्थिति इस प्रकार जांच सकते हैं:\n1. इस चैटबोट में 'स्थिति जांचें' विकल्प का उपयोग करें और अपना FI पंजीकरण/पावती नंबर दर्ज करें।\n2. CKYC पोर्टल (https://www.ckycindia.in) पर जाएं।\n3. अपने वित्तीय संस्थान से संपर्क करें।\n\nस्थिति हो सकती है: जमा किया गया, प्रसंस्करण के अंतर्गत, स्वीकृत, या अस्वीकृत।",
        },
        "training_phrases": [
            "check ckyc application status",
            "track ckyc status",
            "my ckyc application status",
            "ckyc pending status",
            "where is my ckyc",
            "status of my registration",
            "acknowledgment number status",
            "ckyc approved or not",
            "is my ckyc done",
        ],
    },
    {
        "id": "faq_12",
        "category": "General",
        "keywords": ["reporting entity", "entities", "financial institution", "bank", "nbfc", "insurance"],
        "question": {
            "en": "What are Reporting Entities?",
            "hi": "रिपोर्टिंग संस्थाएं क्या हैं?",
        },
        "answer": {
            "en": "Reporting Entities (REs) are financial institutions registered with the Central KYC Registry. These include:\n1. Banks (Public, Private, Foreign, Cooperative)\n2. Insurance Companies\n3. Mutual Fund Companies\n4. Non-Banking Financial Companies (NBFCs)\n5. Payment Banks\n6. Stock Brokers and Depository Participants\n\nAll REs are required to upload KYC records of their customers to the Central KYC Registry.",
            "hi": "रिपोर्टिंग संस्थाएं (RE) सेंट्रल केवाईसी रजिस्ट्री में पंजीकृत वित्तीय संस्थान हैं। इनमें शामिल हैं:\n1. बैंक (सार्वजनिक, निजी, विदेशी, सहकारी)\n2. बीमा कंपनियां\n3. म्यूचुअल फंड कंपनियां\n4. गैर-बैंकिंग वित्तीय कंपनियां (NBFC)\n5. पेमेंट बैंक\n6. स्टॉक ब्रोकर और डिपॉजिटरी पार्टिसिपेंट\n\nसभी RE को अपने ग्राहकों के केवाईसी रिकॉर्ड सेंट्रल केवाईसी रजिस्ट्री में अपलोड करने होते हैं।",
        },
        "training_phrases": [
            "what are reporting entities",
            "what is a reporting entity",
            "list of reporting entities",
            "which financial institutions use ckyc",
            "banks registered with ckyc",
            "who uploads kyc data",
            "reporting entity meaning",
            "RE in ckyc",
        ],
    },
    {
        "id": "faq_13",
        "category": "Technical",
        "keywords": ["api", "integration", "technical", "connect", "system", "software"],
        "question": {
            "en": "How to integrate with CKYC system?",
            "hi": "CKYC सिस्टम के साथ कैसे एकीकरण करें?",
        },
        "answer": {
            "en": "To integrate with the CKYC system:\n1. Register as a Reporting Entity on the CKYC portal.\n2. Obtain API credentials after approval.\n3. Refer to the technical documentation provided by CERSAI.\n4. Implement the APIs for Upload, Search, Download, and Update operations.\n5. Complete the testing in the UAT environment.\n6. Go live after successful testing.\n\nFor technical support, contact the CKYC helpdesk.",
            "hi": "CKYC सिस्टम के साथ एकीकरण के लिए:\n1. CKYC पोर्टल पर रिपोर्टिंग संस्था के रूप में पंजीकरण करें।\n2. अनुमोदन के बाद API क्रेडेंशियल प्राप्त करें।\n3. CERSAI द्वारा प्रदान किए गए तकनीकी दस्तावेज़ देखें।\n4. अपलोड, खोज, डाउनलोड और अपडेट संचालन के लिए API लागू करें।\n5. UAT वातावरण में परीक्षण पूरा करें।\n6. सफल परीक्षण के बाद लाइव करें।\n\nतकनीकी सहायता के लिए, CKYC हेल्पडेस्क से संपर्क करें।",
        },
        "training_phrases": [
            "how to integrate with ckyc",
            "ckyc api integration",
            "technical integration ckyc",
            "connect to ckyc system",
            "ckyc api documentation",
            "how to use ckyc api",
            "software integration ckyc",
        ],
    },
    {
        "id": "faq_14",
        "category": "Security",
        "keywords": ["secure", "security", "safe", "data", "privacy", "protection"],
        "question": {
            "en": "Is my data safe with CKYC?",
            "hi": "क्या CKYC के साथ मेरा डेटा सुरक्षित है?",
        },
        "answer": {
            "en": "Yes, the Central KYC Registry maintains high standards of data security:\n1. All data is encrypted during transmission and storage.\n2. Access to KYC records is strictly controlled and audited.\n3. Only authorized financial institutions can access your data.\n4. The system complies with all applicable data protection regulations.\n5. Regular security audits are conducted.",
            "hi": "हां, सेंट्रल केवाईसी रजिस्ट्री डेटा सुरक्षा के उच्च मानकों को बनाए रखती है:\n1. सभी डेटा प्रसारण और भंडारण के दौरान एन्क्रिप्टेड होता है।\n2. केवाईसी रिकॉर्ड तक पहुंच कड़ाई से नियंत्रित और ऑडिट की जाती है।\n3. केवल अधिकृत वित्तीय संस्थान ही आपके डेटा तक पहुंच सकते हैं।\n4. सिस्टम सभी लागू डेटा संरक्षण नियमों का अनुपालन करता है।\n5. नियमित सुरक्षा ऑडिट किए जाते हैं।",
        },
        "training_phrases": [
            "is my data safe",
            "ckyc data security",
            "is ckyc secure",
            "privacy in ckyc",
            "how is my data protected",
            "data protection ckyc",
            "is kyc data encrypted",
            "who can see my kyc data",
        ],
    },
    {
        "id": "faq_15",
        "category": "Complaints",
        "keywords": ["complaint", "grievance", "issue", "problem", "not working", "error", "help", "support", "contact"],
        "question": {
            "en": "How to raise a complaint?",
            "hi": "शिकायत कैसे दर्ज करें?",
        },
        "answer": {
            "en": "You can raise a complaint through:\n1. The 'Raise Query/Complaint' option in this chatbot (redirects to the web portal).\n2. Writing to support@ckycindia.in\n3. Calling the helpdesk at 1800-XXX-XXXX (toll-free)\n\nOur helpdesk executives are available from 8:00 a.m. to 8:00 p.m., Monday to Saturday.",
            "hi": "आप इनके माध्यम से शिकायत दर्ज कर सकते हैं:\n1. इस चैटबोट में 'प्रश्न/शिकायत दर्ज करें' विकल्प (वेब पोर्टल पर रीडायरेक्ट करता है)।\n2. support@ckycindia.in पर लिखें\n3. 1800-XXX-XXXX (टोल-फ्री) पर हेल्पडेस्क पर कॉल करें\n\nहमारे हेल्पडेस्क कार्यकारी सोमवार से शनिवार, सुबह 8:00 बजे से रात 8:00 बजे तक उपलब्ध हैं।",
        },
        "training_phrases": [
            "how to raise complaint",
            "file a complaint",
            "i have a problem",
            "ckyc not working",
            "complaint about ckyc",
            "grievance redressal",
            "contact ckyc support",
            "help with issue",
            "customer support",
            "helpdesk number",
        ],
    },
    {
        "id": "faq_16",
        "category": "Mismatch",
        "keywords": ["mismatch", "wrong", "incorrect", "different", "not matching", "discrepancy"],
        "question": {
            "en": "What to do if there is a mismatch in CKYC details?",
            "hi": "यदि CKYC विवरण में बेमेल है तो क्या करें?",
        },
        "answer": {
            "en": "If you find a mismatch in your CKYC details:\n1. Contact your Financial Institution (Bank/Insurance/Mutual Fund) where the KYC was originally submitted.\n2. Submit the corrected documents with a request for amendment.\n3. The Financial Institution will upload the corrected details to the Central KYC Registry.\n4. You can also use the 'Mismatch in CKYC Details' option in the API Integration section.\n\nNote: Only the uploading Financial Institution can initiate corrections.",
            "hi": "यदि आपके CKYC विवरण में बेमेल पाया जाता है:\n1. अपने वित्तीय संस्थान (बैंक/बीमा/म्यूचुअल फंड) से संपर्क करें जहां मूल रूप से केवाईसी जमा किया गया था।\n2. संशोधन के अनुरोध के साथ सही दस्तावेज जमा करें।\n3. वित्तीय संस्थान सही विवरण सेंट्रल केवाईसी रजिस्ट्री में अपलोड करेगा।\n4. आप API एकीकरण अनुभाग में 'CKYC विवरण में बेमेल' विकल्प का भी उपयोग कर सकते हैं।\n\nनोट: केवल अपलोड करने वाला वित्तीय संस्थान ही सुधार शुरू कर सकता है।",
        },
        "training_phrases": [
            "mismatch in ckyc details",
            "wrong details in ckyc",
            "incorrect ckyc information",
            "ckyc data not matching",
            "discrepancy in kyc record",
            "my name is wrong in ckyc",
            "wrong address in ckyc",
            "ckyc details are incorrect",
            "how to fix ckyc mismatch",
        ],
    },
    {
        "id": "faq_17",
        "category": "General",
        "keywords": ["portal", "website", "url", "link", "online", "web"],
        "question": {
            "en": "What is the CKYC portal/website?",
            "hi": "CKYC पोर्टल/वेबसाइट क्या है?",
        },
        "answer": {
            "en": "The official CKYC portal is https://www.ckycindia.in. Through this portal, Registered Entities can upload, search, and download KYC records. Individual customers can also search for their CKYC number using their identification details.",
            "hi": "आधिकारिक CKYC पोर्टल https://www.ckycindia.in है। इस पोर्टल के माध्यम से, पंजीकृत संस्थाएं केवाईसी रिकॉर्ड अपलोड, खोज और डाउनलोड कर सकती हैं। व्यक्तिगत ग्राहक भी अपने पहचान विवरण का उपयोग करके अपना CKYC नंबर खोज सकते हैं।",
        },
        "training_phrases": [
            "ckyc portal",
            "ckyc website",
            "ckyc url",
            "official ckyc website",
            "ckyc online portal",
            "website of central kyc",
            "ckyc india website",
            "where is ckyc portal",
        ],
    },
    {
        "id": "faq_18",
        "category": "Wallet",
        "keywords": ["tds", "tax", "deduction", "deducted", "gst"],
        "question": {
            "en": "What about TDS/Tax on CKYC services?",
            "hi": "CKYC सेवाओं पर TDS/कर क्या है?",
        },
        "answer": {
            "en": "TDS (Tax Deducted at Source) is applicable on CKYC services as per the Income Tax Act provisions. The TDS amount is held in the wallet and is adjusted during reconciliation. GST is also applicable on the download charges as per the prevailing rates.",
            "hi": "CKYC सेवाओं पर TDS (स्रोत पर कर कटौती) आयकर अधिनियम के प्रावधानों के अनुसार लागू है। TDS राशि वॉलेट में रखी जाती है और समाधान के दौरान समायोजित की जाती है। डाउनलोड शुल्क पर GST भी प्रचलित दरों के अनुसार लागू है।",
        },
        "training_phrases": [
            "tds on ckyc",
            "tax on ckyc services",
            "gst on ckyc",
            "tax deducted on ckyc",
            "tds deduction ckyc",
            "is gst applicable on ckyc",
            "tax charges ckyc",
        ],
    },
    {
        "id": "faq_19",
        "category": "General",
        "keywords": ["mandatory", "compulsory", "required", "necessary", "must"],
        "question": {
            "en": "Is CKYC mandatory?",
            "hi": "क्या CKYC अनिवार्य है?",
        },
        "answer": {
            "en": "Yes, as per the Prevention of Money Laundering (Maintenance of Records) Rules, 2005, all financial institutions (reporting entities) are mandated to upload KYC data of their clients to the Central KYC Records Registry. This is mandatory for all new accounts/relationships opened with financial institutions.",
            "hi": "हां, धन शोधन निवारण (रिकॉर्ड का रखरखाव) नियम, 2005 के अनुसार, सभी वित्तीय संस्थानों (रिपोर्टिंग संस्थाओं) को अपने ग्राहकों का केवाईसी डेटा सेंट्रल केवाईसी रिकॉर्ड्स रजिस्ट्री में अपलोड करना अनिवार्य है। यह वित्तीय संस्थानों के साथ खोले गए सभी नए खातों/संबंधों के लिए अनिवार्य है।",
        },
        "training_phrases": [
            "is ckyc mandatory",
            "is ckyc compulsory",
            "do i need ckyc",
            "is kyc required by law",
            "ckyc necessary or not",
            "is central kyc mandatory",
            "mandatory ckyc rule",
        ],
    },
    {
        "id": "faq_20",
        "category": "Registration",
        "keywords": ["time", "long", "duration", "days", "how long", "processing time"],
        "question": {
            "en": "How long does CKYC registration take?",
            "hi": "CKYC पंजीकरण में कितना समय लगता है?",
        },
        "answer": {
            "en": "The CKYC registration process typically takes 3-5 working days after the financial institution uploads the KYC data. However, the actual time may vary depending on:\n1. Completeness and accuracy of the submitted documents.\n2. Verification process of the financial institution.\n3. Volume of records being processed.\n\nYou can check the status using the acknowledgment number provided by your financial institution.",
            "hi": "CKYC पंजीकरण प्रक्रिया में आमतौर पर वित्तीय संस्थान द्वारा केवाईसी डेटा अपलोड करने के बाद 3-5 कार्य दिवस लगते हैं। हालांकि, वास्तविक समय निम्न पर निर्भर कर सकता है:\n1. जमा किए गए दस्तावेजों की पूर्णता और सटीकता।\n2. वित्तीय संस्थान की सत्यापन प्रक्रिया।\n3. प्रसंस्कृत किए जा रहे रिकॉर्ड की मात्रा।\n\nआप अपने वित्तीय संस्थान द्वारा प्रदान किए गए पावती नंबर का उपयोग करके स्थिति की जांच कर सकते हैं।",
        },
        "training_phrases": [
            "how long does ckyc take",
            "ckyc processing time",
            "time for ckyc registration",
            "how many days for ckyc",
            "duration of ckyc process",
            "when will my ckyc be done",
            "ckyc turnaround time",
            "kitne din lagta hai ckyc",
        ],
    },
]

# Greeting patterns
GREETINGS = [
    "hello", "hi", "hey", "namaste", "good morning", "good afternoon",
    "good evening", "greetings", "hii", "hiii", "helo", "hllo",
]


# ====== DOMAIN RELEVANCE ======
# Words that indicate the query is related to CKYC domain
DOMAIN_WORDS = {
    "ckyc", "kyc", "central", "registry", "register", "registration",
    "document", "documents", "aadhaar", "pan", "identity", "proof",
    "charges", "charge", "fee", "fees", "cost", "price", "rate",
    "download", "upload", "verification", "verify",
    "wallet", "balance", "recharge", "fund", "tds", "gst", "tax",
    "update", "change", "modify", "correction", "amend", "amendment",
    "status", "track", "application", "pending", "acknowledgment",
    "mismatch", "wrong", "incorrect", "discrepancy",
    "reporting", "entity", "entities", "financial", "institution", "bank",
    "nbfc", "insurance", "mutual",
    "api", "integration", "portal", "website",
    "mandatory", "compulsory",
    "secure", "security", "safe", "privacy", "data", "protection",
    "complaint", "grievance", "support", "helpdesk",
    "benefit", "benefits", "advantage", "purpose",
    "digit", "digits", "number", "14",
    "cersai", "ckycrr",
}


# Topics NOT covered by any FAQ — if query is mainly about these, reject it
OUT_OF_SCOPE = {
    "weather", "temperature", "rain", "sunny", "cold", "hot",
    "centre", "center", "office", "branch", "location", "address", "visit", "nearest",
    "physical", "card", "print", "printed",
    "food", "pizza", "movie", "game", "song", "cricket", "football",
    "name", "age", "joke",
}


def has_domain_relevance(text):
    """Check if user query is relevant to CKYC domain and not out-of-scope."""
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    words = set(cleaned.split())
    has_domain = bool(words & DOMAIN_WORDS)
    has_out_of_scope = bool(words & OUT_OF_SCOPE)

    # If query has out-of-scope words but only generic domain words like "ckyc",
    # treat it as out-of-scope (e.g., "where is ckyc centre")
    if has_out_of_scope and has_domain:
        # Check if the domain words are only generic identifiers
        matched_domain = words & DOMAIN_WORDS
        generic_only = matched_domain <= {"ckyc", "kyc", "central", "registry"}
        if generic_only:
            return False

    return has_domain


# ====== TF-IDF ENGINE ======
class NLPMatcher:
    """TF-IDF + Cosine Similarity based FAQ matcher."""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),     # unigrams + bigrams
            max_df=0.95,
            min_df=1,
            sublinear_tf=True,
        )
        self.faq_indices = []       # maps matrix row -> (faq_index, phrase_type)
        self.tfidf_matrix = None
        self._build_index()

    def _build_index(self):
        """Build TF-IDF matrix from all FAQ questions, answers, and training phrases."""
        corpus = []

        for i, faq in enumerate(FAQS):
            # Add the main question (English)
            corpus.append(preprocess(faq["question"]["en"]))
            self.faq_indices.append(i)

            # Add training phrases
            for phrase in faq.get("training_phrases", []):
                corpus.append(preprocess(phrase))
                self.faq_indices.append(i)

            # Add keywords as a combined phrase
            keywords_text = " ".join(faq.get("keywords", []))
            corpus.append(preprocess(keywords_text))
            self.faq_indices.append(i)

            # Add answer excerpt (first 100 chars for context)
            answer_excerpt = faq["answer"]["en"][:150]
            corpus.append(preprocess(answer_excerpt))
            self.faq_indices.append(i)

        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

    def find_match(self, user_message, threshold=0.30):
        """
        Find best FAQ match using cosine similarity.
        Returns (faq_index, score) or (None, 0).
        """
        # First check: does the query have any CKYC-related words?
        if not has_domain_relevance(user_message):
            return None, 0

        processed = preprocess(user_message)
        if not processed.strip():
            return None, 0

        user_vector = self.vectorizer.transform([processed])
        similarities = cosine_similarity(user_vector, self.tfidf_matrix).flatten()

        # Aggregate scores per FAQ (take max score across all phrases for each FAQ)
        faq_scores = {}
        for idx, score in enumerate(similarities):
            faq_idx = self.faq_indices[idx]
            if faq_idx not in faq_scores or score > faq_scores[faq_idx]:
                faq_scores[faq_idx] = score

        if not faq_scores:
            return None, 0

        best_faq_idx = max(faq_scores, key=faq_scores.get)
        best_score = faq_scores[best_faq_idx]

        if best_score >= threshold:
            return best_faq_idx, best_score

        return None, 0


# Initialize NLP matcher once at module load
nlp_matcher = NLPMatcher()


def get_faq_answer(user_message, lang="en"):
    """
    Get a response for a user message using NLP matching.
    Returns dict with: answer, category, faq_id, matched, is_greeting
    """
    message_lower = user_message.lower().strip()

    # Check for greetings first
    for greeting in GREETINGS:
        if greeting == message_lower or message_lower.startswith(greeting + " ") or message_lower.startswith(greeting + "!"):
            return {
                "answer": None,
                "category": "Greeting",
                "faq_id": None,
                "matched": True,
                "is_greeting": True,
            }

    # NLP-based matching
    faq_idx, score = nlp_matcher.find_match(user_message)

    if faq_idx is not None:
        faq = FAQS[faq_idx]
        return {
            "answer": faq["answer"].get(lang, faq["answer"]["en"]),
            "category": faq.get("category", "General"),
            "faq_id": faq["id"],
            "matched": True,
            "is_greeting": False,
        }

    return {
        "answer": None,
        "category": None,
        "faq_id": None,
        "matched": False,
        "is_greeting": False,
    }

import i18n from "i18next";
import { initReactI18next } from "react-i18next";

i18n.use(initReactI18next).init({
  resources: {
    en: {
      translation: {
        "brand.name":                "Aegis",
        "brand.tagline":             "Authenticity for sport — built for athletes and fans, not the leagues.",
        "nav.athlete":               "Athlete view",
        "nav.rightsHolder":          "Rights-holder dashboard",
        "nav.verify":                "Verify a receipt",
        "athlete.heading":           "Has my likeness been misused?",
        "athlete.subheading":        "Enrol once. Aegis watches the open web for unauthorised use or synthetic media of you, in sport footage and beyond.",
        "athlete.alert.title":       "Your likeness has been misused",
        "athlete.alert.body":        "A synthetic clip depicting you has been detected on {{platform}}. Aegis has drafted takedowns and can file them in one click.",
        "athlete.enrol.cta":         "Enrol to be alerted",
        "athlete.seeTakedowns":      "Review drafted takedowns",
        "rh.heading":                "Rights-holder dashboard",
        "rh.subheading":             "Detections, propagation graph, and agentic takedown across platforms.",
        "verify.heading":            "Verify an Aegis receipt",
        "verify.subheading":         "Every takedown is hashed into a daily Merkle root and signed with a managed key. Anyone can verify a receipt.",
        "verify.input":               "Detection ID",
        "verify.button":              "Verify",
        "constructed.banner":         "Constructed test scenario. Fictional athletes, fictional league. No real person is depicted.",
      },
    },
    hi: {
      translation: {
        "brand.name":                "एजिस",
        "brand.tagline":             "खेल के लिए प्रामाणिकता — खिलाड़ियों और प्रशंसकों के लिए, न कि लीगों के लिए।",
        "nav.athlete":               "खिलाड़ी दृश्य",
        "nav.rightsHolder":          "अधिकार-धारक डैशबोर्ड",
        "nav.verify":                "रसीद सत्यापित करें",
        "athlete.heading":           "क्या मेरी छवि का दुरुपयोग हुआ है?",
        "athlete.subheading":        "एक बार नामांकन करें। एजिस खेल वीडियो में आपकी अनधिकृत या सिंथेटिक मीडिया की तलाश में रहेगा।",
        "athlete.alert.title":       "आपकी छवि का दुरुपयोग हुआ है",
        "athlete.alert.body":        "{{platform}} पर आपकी सिंथेटिक क्लिप पाई गई है। एजिस ने टेकडाउन नोटिस तैयार कर लिए हैं।",
        "athlete.enrol.cta":         "अलर्ट के लिए नामांकन करें",
        "athlete.seeTakedowns":      "तैयार किए गए टेकडाउन देखें",
        "rh.heading":                "अधिकार-धारक डैशबोर्ड",
        "rh.subheading":             "प्लेटफ़ॉर्म पर पहचान, प्रसार ग्राफ़ और एजेंटिक टेकडाउन।",
        "verify.heading":            "एजिस रसीद सत्यापित करें",
        "verify.subheading":         "हर टेकडाउन को दैनिक मर्कल रूट में हैश किया जाता है और प्रबंधित कुंजी से हस्ताक्षरित। कोई भी सत्यापित कर सकता है।",
        "verify.input":               "डिटेक्शन ID",
        "verify.button":              "सत्यापित करें",
        "constructed.banner":         "निर्मित परीक्षण परिदृश्य। काल्पनिक खिलाड़ी, काल्पनिक लीग। किसी वास्तविक व्यक्ति को चित्रित नहीं किया गया है।",
      },
    },
  },
  lng: "en",
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

export default i18n;

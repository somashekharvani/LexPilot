"""
LexPilot - Gemini Analysis Layer
--------------------------------
Performs deep legal document analysis using Google Gemini models:
  - Generates qualitative Attention Flags (🔴 High / 🟠 Review / 🟢 Normal) with bullet-pointed reasons
  - Plain-language rewriting across 3 reading levels (General, Executive, Technical)
  - Suggests "Questions for Your Lawyer"
  - Fallback engine: When GEMINI_API_KEY is not set or network is offline, provides
    high-fidelity rule-and-heuristic analysis that strictly obeys all constraints.
"""

import os
import re
import json
from typing import List, Dict, Any, Tuple, Optional
from ..models.schemas import AttentionLevel, ConfidenceLevel, ReadingLevel

class GeminiClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.client = None
        self._init_client()

    def _init_client(self):
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel("gemini-2.5-flash")
            except Exception as e:
                print(f"[LexPilot] Gemini init warning: {e}")
                self.client = None

    def set_api_key(self, api_key: str):
        self.api_key = api_key
        self._init_client()

    def is_available(self) -> bool:
        return self.client is not None

    def generate(self, prompt: str) -> str:
        if not self.client:
            raise RuntimeError("Gemini client not initialized with valid API key")
        response = self.client.generate_content(prompt, request_options={"timeout": 10.0})
        return response.text

class GeminiAnalyzer:
    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        self.gemini = gemini_client or GeminiClient()

    def analyze_clause(self, clause_data: Dict[str, Any]) -> Tuple[AttentionLevel, List[str], Dict[str, str]]:
        """
        Analyzes a single clause:
          Returns (attention_level, attention_reasons, plain_language_dict)
        """
        title = clause_data.get("title", "")
        text = clause_data.get("text", "")
        category = clause_data.get("category", "other")
        fields = clause_data.get("fields", {})

        if self.gemini.is_available():
            try:
                return self._analyze_with_gemini(title, text, category, fields)
            except Exception as e:
                print(f"[LexPilot] Gemini call failed, falling back: {e}")

        return self._analyze_heuristic(title, text, category, fields)

    def _analyze_with_gemini(self, title: str, text: str, category: str, fields: Dict[str, Any]) -> Tuple[AttentionLevel, List[str], Dict[str, str]]:
        prompt = f"""You are LexPilot, an evidence-grounded legal assistant for paralegals and individuals.
Analyze this legal clause.

STRICT CONSTRAINTS:
1. NEVER output a numeric risk score. Use only qualitative attention levels: High, Review, or Normal.
2. Frame every flag as informational assistance, NOT legal advice or a legal determination.
3. Provide 1 to 3 concise bullet-point reasons citing exact facts from the text.
4. Rewrite the clause into three reading levels:
   - General (8th grade, plain conversational English)
   - Executive (commercial & business impact)
   - Technical (precise legal breakdown for a contract specialist)

CLAUSE CONTEXT:
Title: {title}
Category: {category}
Text:
\"\"\"{text}\"\"\"

Output format: Return strictly valid JSON with this structure:
{{
  "attention_level": "High" or "Review" or "Normal",
  "reasons": ["bullet reason 1", "bullet reason 2"],
  "plain_language": {{
    "general": "Plain 8th-grade explanation",
    "executive": "Executive summary of business impact",
    "technical": "Precise paralegal technical breakdown"
  }}
}}
"""
        response_text = self.gemini.generate(prompt)
        # Parse JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            att_str = data.get("attention_level", "Normal").strip()
            if "High" in att_str:
                att_level = AttentionLevel.HIGH
            elif "Review" in att_str:
                att_level = AttentionLevel.REVIEW
            else:
                att_level = AttentionLevel.NORMAL

            reasons = data.get("reasons", [])
            plain = data.get("plain_language", {})
            return att_level, reasons, plain

        return self._analyze_heuristic(title, text, category, fields)

    def _analyze_heuristic(self, title: str, text: str, category: str, fields: Dict[str, Any]) -> Tuple[AttentionLevel, List[str], Dict[str, str]]:
        """
        High-fidelity heuristic analysis drawing on standard legal contract norms.
        """
        reasons = []
        att_level = AttentionLevel.NORMAL
        text_lower = text.lower()

        # Check category specific high-attention triggers
        if category == "non_compete":
            att_level = AttentionLevel.HIGH
            # Check duration
            dur_match = re.search(r'(\d+)\s+(?:years?|months?)', text_lower)
            duration_str = dur_match.group(0) if dur_match else "indefinite/unspecified period"
            reasons.append(f"Restricts competitive business activities post-termination for {duration_str}.")
            if "worldwide" in text_lower or "any jurisdiction" in text_lower:
                reasons.append("Geographic restriction is exceptionally broad ('worldwide' / all jurisdictions).")
            else:
                reasons.append("Check whether the defined geographic market unreasonably limits future livelihood.")

        elif category == "liability":
            if "unlimited" in text_lower or "shall not apply to" in text_lower or "no event shall" in text_lower:
                att_level = AttentionLevel.HIGH
                reasons.append("Contains limitation of liability exclusions or asymmetric damage waivers.")
            cap_match = re.search(r'(\$\s*\d+(?:,\d{3})*)', text)
            if cap_match:
                reasons.append(f"Specifies explicit monetary aggregate liability cap of {cap_match.group(1)}.")
            else:
                att_level = AttentionLevel.REVIEW
                reasons.append("No explicit dollar liability cap identified in text; damages may be uncapped.")

        elif category == "indemnification":
            att_level = AttentionLevel.HIGH if "hold harmless" in text_lower and "defend" in text_lower else AttentionLevel.REVIEW
            reasons.append("Imposes duty to indemnify, defend, and hold harmless against third-party claims and liabilities.")
            if "attorney's fees" in text_lower or "attorneys' fees" in text_lower or "legal fees" in text_lower:
                reasons.append("Explicitly includes liability for counterparty's legal and attorney's fees.")

        elif category == "termination":
            # Check notice duration
            notice_match = re.search(r'(\d+)\s+days?', text_lower)
            if "without cause" in text_lower or "convenience" in text_lower:
                att_level = AttentionLevel.REVIEW
                days_str = notice_match.group(0) if notice_match else "unspecified"
                reasons.append(f"Permits unilateral termination for convenience upon {days_str} prior written notice.")
            elif "immediate" in text_lower:
                att_level = AttentionLevel.HIGH
                reasons.append("Authorizes immediate termination without cure period upon alleged default.")
            else:
                reasons.append("Standard termination for material breach with contractual cure period.")

        elif category == "payment":
            late_match = re.search(r'(\d+(?:\.\d+)?%)\s*(?:interest|penalty|late fee)?', text_lower)
            if late_match:
                att_level = AttentionLevel.REVIEW
                reasons.append(f"Imposes late payment penalty rate of {late_match.group(1)} per month/annum.")
            amounts = fields.get("monetary_amounts", [])
            if amounts:
                reasons.append(f"Specifies binding payment terms involving {', '.join(amounts)}.")
            else:
                reasons.append("Defines invoicing protocol and payment due windows.")

        elif category == "renewal":
            if "automatic" in text_lower or "evergreen" in text_lower:
                att_level = AttentionLevel.REVIEW
                reasons.append("Automatic renewal clause: Agreement will renew silently unless timely written cancellation is delivered.")
            else:
                reasons.append("Specifies standard non-automatic contract term renewal terms.")

        elif category == "governing_law":
            state_match = re.search(r'state of ([a-z\s]+?)(?:[,\.]|\bthe\b|\bcourts\b)', text_lower)
            jurisdiction = state_match.group(1).title() if state_match else "specified jurisdiction"
            reasons.append(f"Designates governing law under the laws of {jurisdiction}.")
            if "arbitration" in text_lower or "waives jury" in text_lower:
                att_level = AttentionLevel.REVIEW
                reasons.append("Contains mandatory arbitration or jury trial waiver restricting court access.")

        if not reasons:
            reasons.append("Standard operational terms with standard commercial language.")

        # Generate Plain Language Rewrites across 3 reading levels
        plain_language = self._generate_plain_language_heuristic(title, text, category, fields)

        return att_level, reasons, plain_language

    def _generate_plain_language_heuristic(self, title: str, text: str, category: str, fields: Dict[str, Any]) -> Dict[str, str]:
        """
        Generates 3 calibrated reading levels: General, Executive, and Technical.
        """
        # Truncate cleanly for readable presentation
        snippet = text[:300].replace('\n', ' ')

        # General Level (8th Grade English)
        if category == "termination":
            general = f"This section explains how and when either side can end this agreement. It sets out the required warning time and what happens right after cancellation."
            exec_summary = f"Defines contractual exit rights and cure timelines. Affects operational flexibility and continuity of service."
            technical = f"Governs termination triggers (for cause vs. for convenience), notice periods, cure windows, and post-termination survival obligations."

        elif category == "payment":
            money_str = ", ".join(fields.get("monetary_amounts", [])) or "the agreed fees"
            general = f"This section covers how money is paid ({money_str}), when bills must be paid, and whether extra fees apply if payment is late."
            exec_summary = f"Commercial compensation structure governing cash flow, invoicing schedule, and interest penalties on overdue amounts."
            technical = f"Establishes consideration, net payment cycles, billing prerequisites, right of offset, and statutory late payment interest."

        elif category == "non_compete":
            general = f"This rule stops you from working for or starting a competing business for a certain time after this contract ends. Be careful about where and how long this applies."
            exec_summary = f"Post-employment restrictive covenant. Restricts talent mobility and competitive commercial ventures within designated market radius."
            technical = f"Covenant not to compete; imposes restrictive negative obligations regarding market competition, subject to state law reasonableness standards."

        elif category == "liability":
            general = f"This section puts a ceiling on how much money can be paid out if something goes wrong or if there is a lawsuit."
            exec_summary = f"Risk-allocation cap limiting financial exposure to predetermined aggregate sums and disclaiming indirect damages."
            technical = f"Exculpatory clause limiting direct damages to stated cap and expressly disclaiming consequential, special, and punitive damages."

        elif category == "confidentiality":
            general = f"Both sides promise to keep secret information safe and not share private company details with anyone else."
            exec_summary = f"Protects proprietary information and IP assets against unauthorized disclosure or commercial leakage."
            technical = f"Imposes standard of care, definition of proprietary materials, carve-outs for compelled disclosure, and return/destruction mandates."

        elif category == "indemnification":
            general = f"If someone gets sued by a third person because of work done under this contract, one party promises to pay the legal bills and damages."
            exec_summary = f"Shifts third-party legal liability, litigation costs, and settlement expenses to the indemnifying party."
            technical = f"Unilateral or mutual indemnity encompassing defense, settlement, and hold-harmless duties for third-party claims."

        elif category == "governing_law":
            general = f"This decides which state's laws will be used if there is an argument or dispute, and which court will handle it."
            exec_summary = f"Designates legal venue and jurisdiction, governing dispute resolution venue and commercial predictability."
            technical = f"Choice of law and forum selection clause designating substantive jurisdiction and submission to venue."

        else:
            general = f"This section sets out standard rules and requirements for how both parties must work together."
            exec_summary = f"Operational terms defining rights, duties, and procedural mechanics of the transaction."
            technical = f"Miscellaneous contractual provisions establishing binding operational covenants."

        return {
            ReadingLevel.GENERAL.value: general,
            ReadingLevel.EXECUTIVE.value: exec_summary,
            ReadingLevel.TECHNICAL.value: technical
        }

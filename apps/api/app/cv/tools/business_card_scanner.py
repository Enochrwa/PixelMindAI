"""Business Card Scanner CV tool (S1-05).

Extracts: full_name, job_title, company, email[], phone[], website, address, social_handles.
Export: vCard (.vcf), CSV, JSON. Bulk mode: ZIP of multiple card images.
"""

from __future__ import annotations

import csv
import io
import re
from typing import Any
import zipfile

from app.cv.ocr.engine import OCREngine
from app.cv.preprocessing import ImagePreprocessor


class BusinessCardScanner:
    """Extract contact information from business card images."""

    def __init__(self) -> None:
        self._pre = ImagePreprocessor()
        self._ocr = OCREngine(languages=["en", "fr"])

    # ------------------------------------------------------------------
    # Main pipeline
    # ------------------------------------------------------------------

    def process(self, image_bytes: bytes) -> dict[str, Any]:
        """Run the full business card scanning pipeline."""
        img = self._pre.load_image(image_bytes)
        img = self._pre.enhance_contrast(img)

        ocr_result = self._ocr.extract_text(img)
        text: str = str(ocr_result.get("text", ""))
        _raw_conf = ocr_result.get("confidence", 0)
        confidence: int = int(_raw_conf) if isinstance(_raw_conf, (int, float)) else 0

        emails = self._extract_emails(text)
        phones = self._extract_phones(text)
        websites = self._extract_websites(text)
        social = self._extract_social(text)

        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

        return {
            "full_name": self._extract_name(lines, emails, phones),
            "job_title": self._extract_job_title(lines),
            "company": self._extract_company(lines),
            "emails": emails,
            "phones": phones,
            "websites": websites,
            "address": self._extract_address(text),
            "social_handles": social,
            "confidence_score": confidence,
            "raw_text": text,
        }

    def process_bulk(self, images: list[bytes]) -> list[dict[str, Any]]:
        """Process multiple business card images."""
        return [self.process(img_bytes) for img_bytes in images]

    # ------------------------------------------------------------------
    # Export helpers
    # ------------------------------------------------------------------

    def to_vcf(self, result: dict[str, Any]) -> str:
        """Export as vCard (.vcf) format."""
        lines = ["BEGIN:VCARD", "VERSION:3.0"]
        name = result.get("full_name", "")
        if name:
            parts = name.split(" ", 1)
            first = parts[0]
            last = parts[1] if len(parts) > 1 else ""
            lines.append(f"FN:{name}")
            lines.append(f"N:{last};{first};;;")
        if result.get("job_title"):
            lines.append(f"TITLE:{result['job_title']}")
        if result.get("company"):
            lines.append(f"ORG:{result['company']}")
        for email in result.get("emails", []):
            lines.append(f"EMAIL;TYPE=INTERNET:{email}")
        for phone in result.get("phones", []):
            lines.append(f"TEL;TYPE=WORK:{phone}")
        if result.get("address"):
            lines.append(f"ADR;TYPE=WORK:;;{result['address']};;;;")
        for website in result.get("websites", []):
            lines.append(f"URL:{website}")
        lines.append("END:VCARD")
        return "\r\n".join(lines) + "\r\n"

    def to_csv(self, result: dict[str, Any]) -> str:
        """Export as CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Name", "Title", "Company", "Email", "Phone", "Website", "Address"])
        writer.writerow(
            [
                result.get("full_name", ""),
                result.get("job_title", ""),
                result.get("company", ""),
                "; ".join(result.get("emails", [])),
                "; ".join(result.get("phones", [])),
                "; ".join(result.get("websites", [])),
                result.get("address", ""),
            ]
        )
        return output.getvalue()

    def bulk_to_zip(self, results: list[dict[str, Any]], fmt: str = "vcf") -> bytes:
        """Export multiple results as a ZIP archive."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Name", "Title", "Company", "Email", "Phone", "Website", "Address"])
            for i, result in enumerate(results, 1):
                if fmt == "vcf":
                    zf.writestr(f"contact_{i:03d}.vcf", self.to_vcf(result))
                writer.writerow(
                    [
                        result.get("full_name", ""),
                        result.get("job_title", ""),
                        result.get("company", ""),
                        "; ".join(result.get("emails", [])),
                        "; ".join(result.get("phones", [])),
                        "; ".join(result.get("websites", [])),
                        result.get("address", ""),
                    ]
                )
            zf.writestr("contacts_all.csv", output.getvalue())
        return buffer.getvalue()

    # ------------------------------------------------------------------
    # Extraction helpers
    # ------------------------------------------------------------------

    def _extract_emails(self, text: str) -> list[str]:
        pattern = r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
        return list(set(re.findall(pattern, text)))

    def _extract_phones(self, text: str) -> list[str]:
        """Extract phone numbers and normalize to E.164-ish format."""
        phones: list[str] = []
        pattern = r"\+?\d[\d\s\-().]{7,18}\d"
        for match in re.finditer(pattern, text):
            raw = match.group(0).strip()
            normalized = re.sub(r"[^\d+]", "", raw)
            if len(normalized) >= 7:
                phones.append(normalized)
        return list(set(phones))

    def _extract_websites(self, text: str) -> list[str]:
        pattern = r"(?:https?://|www\.)[A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+"
        return list(set(re.findall(pattern, text)))

    def _extract_social(self, text: str) -> dict[str, str]:
        social: dict[str, str] = {}
        patterns = {
            "linkedin": r"(?:linkedin\.com/in/|@)([A-Za-z0-9_\-]+)",
            "twitter": r"(?:twitter\.com/|x\.com/|@)([A-Za-z0-9_]{1,15})",
            "instagram": r"(?:instagram\.com/|@)([A-Za-z0-9_.]{1,30})",
        }
        for platform, pat in patterns.items():
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                social[platform] = match.group(1)
        return social

    def _extract_name(self, lines: list[str], _emails: list[str], phones: list[str]) -> str | None:
        """Heuristic: name is usually the first line that looks like a name."""
        for line in lines[:5]:
            if any(x in line.lower() for x in ["@", "http", "www.", "+", "tel", "fax"]):
                continue
            if any(
                p in re.sub(r"\D", "", line) for p in [re.sub(r"\D", "", p) for p in phones if p]
            ):
                continue
            words = line.split()
            name_ok = all(re.match(r"^[A-Za-z\-\.\']+$", w) for w in words)
            if 2 <= len(words) <= 4 and name_ok:
                return line.strip()
        return lines[0] if lines else None

    def _extract_job_title(self, lines: list[str]) -> str | None:
        title_keywords = [
            "ceo",
            "cto",
            "coo",
            "cfo",
            "founder",
            "director",
            "manager",
            "engineer",
            "developer",
            "designer",
            "consultant",
            "analyst",
            "officer",
            "president",
            "vice president",
            "vp",
            "head of",
            "lead",
            "senior",
            "associate",
            "intern",
        ]
        for line in lines[1:8]:
            if any(kw in line.lower() for kw in title_keywords):
                return line.strip()
        return None

    def _extract_company(self, lines: list[str]) -> str | None:
        company_keywords = [
            "ltd",
            "llc",
            "inc",
            "corp",
            "co.",
            "group",
            "technologies",
            "solutions",
            "consulting",
            "services",
            "systems",
            "global",
            "africa",
            "international",
        ]
        for line in lines:
            if any(kw in line.lower() for kw in company_keywords):
                return line.strip()
        return None

    def _extract_address(self, text: str) -> str | None:
        pattern = (
            r"\d+\s+[A-Za-z\s,]{5,80}"
            r"(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way|Place|Pl)"
        )
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(0) if match else None

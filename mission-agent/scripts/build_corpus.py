"""Turn public NIST PDFs into text chunks for retrieval.

Usage: python3 mission-agent/scripts/build_corpus.py <pdf_dir> [output_csv]
<pdf_dir> holds the downloaded PDFs (see DOCS for names and source URLs). NIST publications are
US government works. Chunks are about 200 words with 40 words of overlap, split within a page,
so every chunk keeps a page number for citations.
"""
import csv
import os
import re
import sys

from pypdf import PdfReader

DOCS = {  # file name -> (doc_id, title, source URL)
    "csf2.pdf": ("CSF2", "NIST Cybersecurity Framework 2.0", "https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf"),
    "sp800-61r3.pdf": ("SP800-61r3", "NIST SP 800-61 Rev. 3, Incident Response Recommendations",
                       "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r3.pdf"),
    "sp800-37r2.pdf": ("SP800-37r2", "NIST SP 800-37 Rev. 2, Risk Management Framework",
                       "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-37r2.pdf"),
}
WORDS, OVERLAP = 200, 40


def clean(t):
    t = re.sub(r"-\n(?=[a-z])", "", t)
    t = t.replace("\u2013", "-").replace("\u2014", "-")  # repo rule: no em or en dashes
    t = re.sub(r"\s+", " ", t).strip()
    # PDF extraction sometimes splits control identifiers such as "PR.DS-01" into "P R.DS- 01".
    t = re.sub(r"\b([A-Z]) ([A-Z]\.[A-Z]{2})- ?(\d{2})\b", r"\1\2-\3", t)
    t = re.sub(r"\b([A-Z]{1,2}\.[A-Z]{2})- (\d{2})\b", r"\1-\2", t)
    return re.sub(r"\bT he\b", "The", t)


def main():
    pdf_dir = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "mission-agent/data/nist_chunks.csv"
    n = 0
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["chunk_id", "doc_id", "title", "source_url", "page", "text"])
        for fname, (doc_id, title, url) in DOCS.items():
            for p, page in enumerate(PdfReader(os.path.join(pdf_dir, fname)).pages, 1):
                words = clean(page.extract_text() or "").split()
                step = WORDS - OVERLAP
                for i in range(0, max(len(words), 1), step):
                    piece = words[i:i + WORDS]
                    if len(piece) < 40:
                        break
                    n += 1
                    w.writerow([f"{doc_id}-p{p}-{i // step}", doc_id, title, url, p, " ".join(piece)])
    print(n, "chunks")


if __name__ == "__main__":
    main()

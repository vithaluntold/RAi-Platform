"""Financial statement mappings - normalize financial document names."""

# Comprehensive financial statement name synonyms mapping
# Maps various real-world financial statement names to standardized forms
FINANCIAL_STATEMENT_MAPPINGS = {
    # Balance Sheet variants
    "balance sheet": "Balance Sheet",
    "statement of financial position": "Balance Sheet",
    "statement of financial status": "Balance Sheet",
    "assets and liabilities": "Balance Sheet",
    "financial position": "Balance Sheet",
    
    # Income Statement variants
    "income statement": "Income Statement",
    "statement of comprehensive income": "Statement of Comprehensive Income",
    "statement of profit and loss": "Income Statement",
    "profit and loss": "Income Statement",
    "p&l": "Income Statement",
    "p & l": "Income Statement",
    "statement of financial performance": "Statement of Comprehensive Income",
    "comprehensive income": "Statement of Comprehensive Income",
    
    # Cash Flow Statement variants
    "cash flow statement": "Statement of Cashflows",
    "statement of cash flows": "Statement of Cashflows",
    "statement of cashflows": "Statement of Cashflows",
    "cashflows": "Statement of Cashflows",
    "cash flows": "Statement of Cashflows",
    "cash flow": "Statement of Cashflows",
    
    # Statement of Changes in Equity variants
    "statement of changes in equity": "Statement of Changes in Equity",
    "statement of shareholders equity": "Statement of Changes in Equity",
    "statement of retained earnings": "Statement of Changes in Equity",
    "changes in equity": "Statement of Changes in Equity",
    "equity statement": "Statement of Changes in Equity",
    
    # Notes to Financial Statements
    "notes to financial statements": "Notes to Financial Statements",
    "notes to accounts": "Notes to Financial Statements",
    "footnotes": "Notes to Financial Statements",
    "notes": "Notes to Financial Statements",
}

# Optional: Define financial statement categories
FINANCIAL_STATEMENT_CATEGORIES = {
    "Balance Sheet": ["balance sheet", "statement of financial position"],
    "Income Statement": ["income statement", "profit and loss", "p&l"],
    "Statement of Comprehensive Income": ["comprehensive income", "statement of profit and loss"],
    "Statement of Cashflows": ["cash flow", "cashflows"],
    "Statement of Changes in Equity": ["equity statement", "changes in equity"],
    "Notes to Financial Statements": ["notes", "footnotes"],
}

__all__ = [
    "FINANCIAL_STATEMENT_MAPPINGS",
    "FINANCIAL_STATEMENT_CATEGORIES",
]

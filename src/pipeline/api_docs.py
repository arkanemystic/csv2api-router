"""API documentation and usage guidelines."""

API_USAGE_GUIDE = '''
1️⃣ fill_account_by
Purpose: Add funds to a given account.

Params:
- account_id (string): ID of the account
- amount (number): Amount to add

Use when:
- The user asks to fill, credit, top up, or add funds to accounts.
- Example prompts:
    - "Fill accounts with provided amounts."
    - "Credit these accounts."
    - "Top up each account."
    - "Fill_account_by these accounts."
- The CSV should contain columns for account_id and amount.

==========================

2️⃣ get_transaction
Purpose: Retrieve full details of a blockchain transaction.

Params:
- chain (string): Blockchain name (e.g. ETHEREUM)
- tx_hash (string): Transaction hash

Use when:
- The user asks to get transaction details, retrieve full transaction, look up a transaction, etc.
- Example prompts:
    - "Get full details of these transactions."
    - "Fetch transaction information."
    - "Retrieve blockchain transactions."

==========================

3️⃣ tag_as_expense
Purpose: Mark a transaction as an expense.

Params:
- chain (string): Blockchain name
- tx_hash (string): Transaction hash
- expense_category (string): Category of the expense

Use when:
- The user asks to tag transactions as expenses, categorize transactions, mark as expense, etc.
- Example prompts:
    - "Tag all these transactions as office expenses."
    - "Mark these as marketing expenses."
    - "Categorize these transactions."

==========================

4️⃣ get_receipt
Purpose: Retrieve the blockchain receipt for a transaction.

Params:
- chain (string): Blockchain name
- tx_hash (string): Transaction hash

Use when:
- The user asks to get receipt(s), retrieve receipt(s), download receipt(s), fetch receipts, etc.
- Example prompts:
    - "Get receipts for these transactions."
    - "Fetch blockchain receipts."
    - "Retrieve the receipts."

==========================

5️⃣ list_chains
Purpose: List supported blockchain chains.

Params:
- None (empty param list)

Use when:
- The user asks to list chains, show supported blockchains, fetch available chains, etc.
- Example prompts:
    - "List all supported blockchains."
    - "Show available chains."
    - "What chains can I use?"
'''

INTENT_ANALYSIS_PROMPT = '''
Given the following user prompt:
"{user_prompt}"

And considering the API usage guidelines above, determine:
1. Which API method best matches the user's intent
2. Why this API is the best choice
3. What parameters will be needed from the CSV data

Respond in the following JSON format only:
{
    "api_method": "name_of_api_method",
    "reasoning": "brief explanation of why this API was chosen",
    "required_params": ["list", "of", "required", "parameters"],
    "confidence": 0.XX  // confidence score between 0 and 1
}
''' 
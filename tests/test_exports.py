import pytest
from ermi.exports import categorize_chat

@pytest.mark.parametrize(
    "title, full_text, expected",
    [
        # Code block takes precedence
        ("Creative Story", "Here is some code:\n```python\nprint('hello')\n```", "Code"),
        ("Project Plan", "```javascript\nconsole.log(1);\n```", "Code"),
        # Creative writing keywords match
        ("My Novel Chapter 1", "Just text", "Creative_Writing"),
        ("Character backstory", "More text", "Creative_Writing"),
        ("POEM about spring", "No code here", "Creative_Writing"),
        # Project keywords match
        ("Q1 Strategy", "Text", "Projects_and_Protocols"),
        ("SOP for deployment", "Text", "Projects_and_Protocols"),
        ("Meeting notes", "Text", "Projects_and_Protocols"),
        # Default fallback
        ("Random chat", "Some random text", "General"),
        ("Untitled Chat", "", "General"),
        # Edge cases
        ("", "", "General"),  # Empty strings
        ("STORY", "Some text", "Creative_Writing"), # Case insensitivity
        ("stOry", "Some text", "Creative_Writing"), # Case insensitivity
        ("sops", "Some text", "Projects_and_Protocols"), # Substring match (sops contains sop)
    ],
)
def test_categorize_chat(title: str, full_text: str, expected: str) -> None:
    assert categorize_chat(title, full_text) == expected

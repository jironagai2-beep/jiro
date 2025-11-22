# CLAUDE.md - AI Assistant Guide

This document provides comprehensive guidance for AI assistants working with the Jiro password generator codebase.

## Project Overview

**Jiro** is a simple, bilingual (Japanese/English) password generator written in Python. The tool provides two modes of password generation:

1. **Random passwords**: Strong passwords using combinations of uppercase, lowercase, digits, and special characters
2. **Memorable passwords**: Word-based passwords that are easier to remember

**Project Type**: CLI utility
**Language**: Python 3.6+
**Primary File**: `password_generator.py` (165 lines)
**Documentation**: Bilingual README.md (Japanese/English)

## Repository Structure

```
jiro/
├── password_generator.py    # Main executable (CLI tool)
├── README.md                # Bilingual project documentation
└── CLAUDE.md                # This file - AI assistant guidance
```

**Key Points**:
- This is a single-file project with minimal dependencies
- No external packages required (uses only Python stdlib: `random`, `string`, `argparse`)
- The executable bit is set on `password_generator.py` for direct execution

## Core Functionality

### Main Functions

1. **`generate_password()`** (lines 12-45)
   - Generates random character-based passwords
   - Parameters: length, use_uppercase, use_lowercase, use_digits, use_special
   - Returns: String password

2. **`generate_memorable_password()`** (lines 48-80)
   - Generates word-based memorable passwords
   - Uses a hardcoded list of 24 simple English words
   - Parameters: num_words, separator, capitalize, add_number
   - Returns: String password (e.g., "Dragon-Forest-Happy-Ocean42")

3. **`main()`** (lines 83-161)
   - CLI entry point using argparse
   - Handles argument parsing and output formatting

### CLI Arguments

- `-l, --length`: Password length (default: 12)
- `-n, --count`: Number of passwords to generate (default: 1)
- `--no-uppercase/lowercase/digits/special`: Exclude character types
- `-m, --memorable`: Generate word-based password
- `-w, --words`: Number of words for memorable passwords (default: 4)

## Key Conventions

### 1. Bilingual Everything

**CRITICAL**: This project is fully bilingual (Japanese/English). When modifying or extending:

- **Code comments**: Provide both Japanese and English
  ```python
  # 日本語の説明 / English explanation
  ```
- **Docstrings**: Include both languages
- **User-facing messages**: Display both languages
- **Documentation**: Update README.md with both Japanese and English sections
- **Commit messages**: Write in both languages (Japanese first, then English)

### 2. Code Style

- **Shebang**: Uses `#!/usr/bin/env python3`
- **Docstrings**: Google-style with bilingual descriptions
- **String formatting**: Uses f-strings (Python 3.6+)
- **Line length**: Reasonable (not strictly enforced)
- **Imports**: Standard library only, alphabetically organized

### 3. User Experience

- Output includes emoji (🔐) for visual appeal
- Clean formatting with separators (`=` * 50)
- Numbered output when generating multiple passwords
- Bilingual help text in argparse

## Development Workflows

### Testing the Tool

```bash
# Basic test - generate one password
python3 password_generator.py

# Test with various options
python3 password_generator.py -l 20 -n 3
python3 password_generator.py -m -w 5
python3 password_generator.py --no-special --no-digits

# Direct execution (file has executable bit)
./password_generator.py
```

### Making Changes

When modifying the code:

1. **Read first**: Always read `password_generator.py` before making changes
2. **Preserve bilingual nature**: Add Japanese and English for all user-facing text
3. **Test thoroughly**: Run the tool with various argument combinations
4. **Update README.md**: Document new features in both languages
5. **Maintain simplicity**: This is intentionally a simple, single-file tool

### Adding New Features

When adding features, consider:

- **Word list expansion**: The memorable password word list (lines 63-68) could be expanded
- **Character sets**: Custom character sets for specific requirements
- **Output formats**: JSON, CSV, or other formats for integration
- **Security enhancements**: Cryptographically secure random number generation
- **Configuration files**: Support for `.passwordrc` or similar

**Important**: Discuss significant architectural changes before implementing.

## Git Workflow

### Branch Naming

- Feature branches: Use the pattern `claude/claude-md-<session-id>`
- Current branch: `claude/claude-md-mia6gxq7im6ttx19-01FUFyxD4mMSKk5vNbrJvz3X`

### Commit Messages

Follow the established pattern:

```
日本語の説明 / English explanation

More details if needed (bilingual)
```

Example from history:
```
簡単なパスワードジェネレーターを実装 / Implement simple password generator
```

### Pushing Changes

```bash
# Always push to the feature branch with -u flag
git push -u origin claude/claude-md-<session-id>

# Retry on network failures with exponential backoff (2s, 4s, 8s, 16s)
```

## Code Modification Guidelines

### Security Considerations

This is a password generator, so security is paramount:

1. **Do NOT weaken randomness**: The `random` module is used, which is not cryptographically secure for production use, but suitable for this tool's scope
2. **Consider `secrets` module**: For enhanced security, consider using `secrets.choice()` instead of `random.choice()`
3. **Validate input**: Ensure at least one character type is selected
4. **No password storage**: This tool generates passwords but does not store them
5. **Clear output**: Passwords are printed to stdout (consider security implications for shell history)

### What to Avoid

1. **Over-engineering**: Keep it simple - this is a single-file CLI tool
2. **External dependencies**: Avoid adding packages unless absolutely necessary
3. **Breaking changes**: Maintain backward compatibility with existing CLI arguments
4. **Removing bilingual support**: Never remove Japanese or English text
5. **Complex abstractions**: Direct, readable code is preferred

### What to Preserve

1. **Bilingual nature**: All text in both Japanese and English
2. **Simple architecture**: Single-file structure
3. **CLI interface**: Existing argument names and behavior
4. **Output format**: The visual style with emoji and separators
5. **Python 3.6+ compatibility**: No features requiring newer Python versions unless justified

## Common Tasks

### Adding a New CLI Argument

1. Add argument to `parser` in `main()` with bilingual help text
2. Handle the argument in the password generation logic
3. Update README.md with usage examples (bilingual)
4. Test with various combinations

### Expanding the Word List

1. Locate the `words` list in `generate_memorable_password()` (line 63)
2. Add words that are:
   - Simple and common English words
   - Easy to type
   - 4-8 characters long
   - Family-friendly
3. Keep alphabetical organization if possible

### Improving Security

Consider these enhancements:

```python
import secrets  # Instead of random

# In generate_password()
password = ''.join(secrets.choice(characters) for _ in range(length))

# In generate_memorable_password()
selected_words = [secrets.choice(words) for _ in range(num_words)]
number = secrets.randbelow(90) + 10  # 10-99
```

## Testing Checklist

Before committing changes:

- [ ] Code runs without errors: `python3 password_generator.py`
- [ ] All CLI arguments work as expected
- [ ] Bilingual text is present for all new features
- [ ] README.md is updated (if adding features)
- [ ] No external dependencies added (or justified if needed)
- [ ] Output format is preserved
- [ ] Edge cases handled (e.g., all character types excluded)

## Python-Specific Notes

### Standard Library Modules Used

- `random`: Pseudo-random number generation (consider `secrets` for crypto-strength)
- `string`: Character constants (ascii_uppercase, ascii_lowercase, digits, punctuation)
- `argparse`: Command-line argument parsing

### Error Handling

Currently minimal error handling:
- ValueError raised if no character types selected
- argparse handles invalid argument types

**Enhancement opportunity**: Add try/except in main() for better error messages.

## Questions for the User

When uncertain about changes, ask:

1. **Bilingual text**: "Should I add this message in both Japanese and English?"
2. **Security**: "Should we use the `secrets` module for cryptographic randomness?"
3. **Dependencies**: "This feature would benefit from package X - is adding a dependency acceptable?"
4. **Breaking changes**: "This would change the existing CLI behavior - should we proceed?"
5. **Scope**: "This is beyond a simple CLI tool - should we expand the project scope?"

## Additional Resources

### Python Documentation

- argparse: https://docs.python.org/3/library/argparse.html
- secrets module: https://docs.python.org/3/library/secrets.html
- string constants: https://docs.python.org/3/library/string.html

### Password Security Best Practices

- Use cryptographically secure random (secrets module)
- Minimum length: 12-16 characters
- Include multiple character types
- Avoid dictionary words (except in memorable passwords with sufficient entropy)

## Version History

- **Initial commit** (9cbe202): 簡単なパスワードジェネレーターを実装 / Implement simple password generator
  - Single-file password generator
  - Bilingual documentation
  - Random and memorable password modes
  - Comprehensive CLI options

---

**Last Updated**: 2025-11-22
**Project Status**: Active
**Maintainer Preferences**: Simplicity, bilingual support, security-conscious

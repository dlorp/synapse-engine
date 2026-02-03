# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

_No unreleased changes._

## [5.1.0] - 2025-02-03

### Added
- Integration tests for CGRAG context retrieval
- Version badge to README
- Comprehensive tests for QueryExpander service

### Changed
- Improved backend test coverage for models

### Fixed
- Improved Mermaid diagram contrast for better readability

## [5.0.0] - 2025-02-01

### Added
- CGRAG path traversal security validation with comprehensive tests
- Query expander unit tests for improved coverage
- Frontend README with development setup and component documentation
- Scripts README documenting all utility scripts
- Architecture documentation with Mermaid diagrams
- Complete API reference documentation

### Changed
- Refactored code chat functionality removed (use opencode instead)
- Improved CONTRIBUTING.md with detailed guidelines
- Reorganized backend README for clarity
- Enhanced docs/README.md structure

### Fixed
- Resolved mypy type errors across codebase
- Fixed 6 failing tests in test_code_chat_tools.py and test_crag.py
- Fixed profile system and query router edge cases
- Renamed test_active_moderator to avoid pytest fixture error
- Resolved CI hang by moving websocket script to scripts/

### Docs
- Comprehensive documentation cleanup and improvements
- Added Metal acceleration guide (docs/METAL.md)
- Added security documentation (docs/SECURITY.md)
- Added CGRAG documentation (docs/CGRAG.md)

[Unreleased]: https://github.com/dlorp/synapse-engine/compare/v5.1.0...HEAD
[5.1.0]: https://github.com/dlorp/synapse-engine/compare/v5.0.0...v5.1.0
[5.0.0]: https://github.com/dlorp/synapse-engine/releases/tag/v5.0.0

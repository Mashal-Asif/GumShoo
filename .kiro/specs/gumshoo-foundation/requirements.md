# Requirements Document

## Introduction

GumShoo is a social media safety detector application that analyzes social media content for risk across four detection domains: deepfake images, sentiment analysis, fraud detection, and propaganda detection. This specification defines the foundation rebuild of GumShoo, creating an application shell with navigation, input handling, tool registry, result schema, theming, settings, and quality infrastructure. The scope explicitly excludes real model implementations; each tool will use stub implementations that return clearly flagged demo results.

## Glossary

- **Application**: The GumShoo social media safety detector system
- **Tool**: A pluggable analysis module (Deepfake Analyzer, Sentiment Analysis, Fraud Detection, Propaganda Detection)
- **Tool_Registry**: The central registration and discovery system for analysis tools
- **Input_Reader**: A component that safely reads and validates input from various sources
- **Result_Schema**: The standardized data structure returned by all analysis tools
- **Welcome_Page**: The landing page displaying the four tool cards
- **Input_Page**: The shared input collection page used by all tools
- **Result_Page**: The page displaying analysis results with tool-specific renderers
- **Status_Panel**: A UI component showing the operational state of each tool's model
- **Theme**: The visual styling configuration including colors, fonts, and contrast ratios
- **Demo_Mode**: A tool operational state using stub implementations instead of real models
- **User_Content**: Any text, image, or data provided by users for analysis
- **Private_Address**: IP addresses in private ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
- **Loopback_Address**: IP addresses referring to localhost (127.0.0.0/8, ::1)
- **Link_Local_Address**: IP addresses in link-local range (169.254.0.0/16, fe80::/10)

## Requirements

### Requirement 1: Welcome Page

**User Story:** As an analyst, I want to see all available detection tools on the welcome page, so that I can select the appropriate tool for my analysis task.

#### Acceptance Criteria

1.1. THE Welcome_Page SHALL display exactly four tool cards numbered Module 01 through Module 04

1.2. THE Welcome_Page SHALL label the four tool cards as "Deepfake Analyzer", "Sentiment Analysis", "Fraud Detection", and "Propaganda Detection"

1.3. THE Welcome_Page SHALL exclude emoji characters from all displayed text

1.4. WHEN a user clicks a tool card, THE Application SHALL navigate to the Input_Page

### Requirement 2: Shared Input Page

**User Story:** As an analyst, I want to provide input through a single consistent interface, so that I can quickly submit content for analysis regardless of which tool I am using.

#### Acceptance Criteria

2.1. THE Input_Page SHALL accept input via text paste or file upload

2.2. THE Input_Page SHALL accept file uploads with extensions png, jpg, jpeg, webp, docx, txt, and csv

2.3. WHEN a user uploads a file with an unsupported extension, THE Input_Page SHALL display a clear error message

2.4. WHEN a user uploads a file exceeding the size limit, THE Input_Page SHALL display a clear error message specifying the size limit

2.5. WHERE the selected tool accepts text input, THE Input_Page SHALL offer options for "separate posts" or "one whole document" processing modes

2.6. WHEN a user uploads a CSV file, THE Input_Page SHALL process the file row by row

2.7. WHEN a user uploads a CSV file, THE Input_Page SHALL auto-detect the text column for analysis

2.8. THE Input_Page SHALL validate input type compatibility with the selected tool

### Requirement 3: Input Readers

**User Story:** As a security-conscious system administrator, I want input readers to enforce safety constraints, so that the application cannot be exploited to access unauthorized resources or execute malicious content.

#### Acceptance Criteria

3.1. THE Input_Reader SHALL extract text content from docx files

3.2. THE Input_Reader SHALL extract embedded images from docx files

3.3. THE Input_Reader SHALL read text content from txt files

3.4. THE Input_Reader SHALL parse and read csv files

3.5. THE Input_Reader SHALL fetch content from URLs with http or https schemes only

3.6. IF a URL uses a scheme other than http or https, THEN THE Input_Reader SHALL reject the request with an error message

3.7. WHEN fetching content from a URL, THE Input_Reader SHALL enforce a timeout limit

3.8. WHEN fetching content from a URL, THE Input_Reader SHALL enforce a content size limit

3.9. IF a URL resolves to a Private_Address, THEN THE Input_Reader SHALL reject the request with an error message

3.10. IF a URL resolves to a Loopback_Address, THEN THE Input_Reader SHALL reject the request with an error message

3.11. IF a URL resolves to a Link_Local_Address, THEN THE Input_Reader SHALL reject the request with an error message

3.12. THE Input_Reader SHALL validate file encoding and handle encoding errors gracefully

### Requirement 4: Tool Plugin Interface and Registry

**User Story:** As a developer, I want to add new analysis tools through a standard interface, so that I can extend the application without modifying core infrastructure.

#### Acceptance Criteria

4.1. THE Tool_Registry SHALL provide a registration mechanism for tools

4.2. WHEN a tool registers, THE Tool_Registry SHALL require the tool to declare a name

4.3. WHEN a tool registers, THE Tool_Registry SHALL require the tool to declare accepted input types

4.4. WHEN a tool registers, THE Tool_Registry SHALL require the tool to provide an analyse function

4.5. THE Tool_Registry SHALL allow discovery of registered tools by name

4.6. THE Tool_Registry SHALL allow discovery of registered tools by accepted input type

### Requirement 5: Result Schema

**User Story:** As an analyst, I want all analysis results to follow a consistent structure, so that I can interpret results uniformly across different tools.

#### Acceptance Criteria

5.1. THE Result_Schema SHALL include a label field

5.2. THE Result_Schema SHALL include a score field with values ranging from 0 to 1 inclusive

5.3. THE Result_Schema SHALL include a details field

5.4. THE Result_Schema SHALL include a warnings field

5.5. THE Result_Schema SHALL include a model_name field

5.6. THE Result_Schema SHALL include a model_version field

5.7. THE Result_Schema SHALL include an is_demo field indicating whether the result is from a stub implementation

5.8. WHEN a tool returns a score, THE Result_Schema SHALL constrain the score to the range 0 to 1 inclusive

### Requirement 6: Result Pages

**User Story:** As an analyst, I want to view analysis results with appropriate context and disclaimers, so that I understand the limitations and uncertainty of the analysis.

#### Acceptance Criteria

6.1. THE Result_Page SHALL display a visible notice stating "estimate, not a verdict"

6.2. THE Result_Page SHALL provide a generic result renderer for all tools

6.3. THE Result_Page SHALL provide tool-specific result renderers

6.4. THE Result_Page SHALL offer CSV download of results

6.5. THE Result_Page SHALL offer JSON download of results

6.6. THE Result_Page SHALL display the label field from the Result_Schema

6.7. THE Result_Page SHALL display the score field from the Result_Schema

6.8. THE Result_Page SHALL display the details field from the Result_Schema

6.9. THE Result_Page SHALL display the warnings field from the Result_Schema

6.10. THE Result_Page SHALL display the model_name field from the Result_Schema

6.11. THE Result_Page SHALL display the model_version field from the Result_Schema

6.12. WHEN is_demo is true, THE Result_Page SHALL display a visible indicator that results are from a demo stub

### Requirement 7: Theme and Visual Design

**User Story:** As an analyst, I want the interface to use professional styling with sufficient contrast, so that I can work comfortably for extended periods and meet accessibility standards.

#### Acceptance Criteria

7.1. THE Theme SHALL use a pastel lavender color in the color palette

7.2. THE Theme SHALL use a soft green color in the color palette

7.3. THE Theme SHALL use a soft pink color in the color palette

7.4. THE Theme SHALL use serif fonts for heading text

7.5. THE Theme SHALL meet WCAG AA contrast ratio requirements for all text

7.6. THE Theme SHALL be defined in a CSS stylesheet

7.7. THE Theme SHALL be defined in a Streamlit theme configuration file

7.8. THE Application SHALL exclude emoji characters from all user interface elements

7.9. THE Application SHALL exclude emoji characters from all code comments

7.10. THE Application SHALL exclude emoji characters from all documentation

### Requirement 8: Status Panel

**User Story:** As an analyst, I want to see the operational status of each tool, so that I understand whether I am viewing real analysis or demo results.

#### Acceptance Criteria

8.1. THE Status_Panel SHALL display the model state for each registered tool

8.2. THE Status_Panel SHALL indicate when a tool model is in "loaded" state

8.3. THE Status_Panel SHALL indicate when a tool model is in "fallback" state

8.4. THE Status_Panel SHALL indicate when a tool model is in "demo" state

8.5. WHEN a tool's model file is missing, THE Status_Panel SHALL display a warning message

8.6. IF a tool's model file is missing, THEN THE Application SHALL operate in fallback or demo mode

8.7. IF a tool's model file is missing, THEN THE Application SHALL NOT terminate or crash

### Requirement 9: Data Privacy

**User Story:** As a privacy-conscious user, I want my uploaded content to be processed ephemerally, so that my data is not retained after analysis.

#### Acceptance Criteria

9.1. THE Application SHALL NOT persist uploaded files to disk

9.2. THE Application SHALL NOT write User_Content to application logs

9.3. THE Application SHALL process uploaded content in memory only

9.4. WHEN analysis completes, THE Application SHALL discard User_Content from memory

### Requirement 10: Quality and Testing

**User Story:** As a developer, I want comprehensive testing and code quality checks, so that I can maintain and extend the codebase with confidence.

#### Acceptance Criteria

10.1. THE Application SHALL include pytest tests for all Input_Reader components

10.2. THE Application SHALL include pytest tests for the Tool_Registry

10.3. THE Application SHALL include pytest tests for the Result_Schema

10.4. WHEN ruff is executed on the codebase, THE Application SHALL produce zero linting violations

10.5. THE Application SHALL include type hints for all public functions

10.6. THE Application SHALL include docstrings for all public functions

10.7. THE Application SHALL include docstrings for all public classes

### Requirement 11: Configuration and Deployment

**User Story:** As a system administrator, I want clear setup instructions and secure configuration management, so that I can deploy the application on Windows systems.

#### Acceptance Criteria

11.1. THE Application SHALL include a README file with Windows PowerShell setup instructions

11.2. THE Application SHALL store application settings in a YAML configuration file

11.3. THE Application SHALL store secrets in a .env file

11.4. THE Application SHALL include a requirements.txt file with pinned dependency versions

11.5. THE Application SHALL execute successfully on Windows using PowerShell

11.6. THE Application SHALL include a .gitignore entry for the models directory

11.7. THE Application SHALL include a .gitignore entry for dataset files

11.8. THE Application SHALL include a .gitignore entry for the .env file

### Requirement 12: Tool Stub Implementations

**User Story:** As a developer building the foundation, I want placeholder tool implementations, so that I can validate the architecture without waiting for real models.

#### Acceptance Criteria

12.1. THE Application SHALL include a stub implementation for the Deepfake Analyzer tool

12.2. THE Application SHALL include a stub implementation for the Sentiment Analysis tool

12.3. THE Application SHALL include a stub implementation for the Fraud Detection tool

12.4. THE Application SHALL include a stub implementation for the Propaganda Detection tool

12.5. WHEN a stub tool analyzes content, THE Tool SHALL return a Result_Schema with is_demo set to true

12.6. WHEN a stub tool analyzes content, THE Tool SHALL return clearly identifiable demo data in the result fields

12.7. THE stub implementations SHALL NOT attempt to load real model weights

### Requirement 13: Project Structure

**User Story:** As a developer, I want a clear and consistent project structure, so that I can locate and organize code efficiently.

#### Acceptance Criteria

13.1. THE Application SHALL organize Streamlit entry point and pages in an app directory

13.2. THE Application SHALL organize tool registry, result schema, input readers, and settings in a core directory

13.3. THE Application SHALL organize tool implementations in a tools directory with one package per tool

13.4. THE Application SHALL organize model files and model cards in a models directory

13.5. THE Application SHALL organize CSS stylesheets and theme configuration in an assets directory

13.6. THE Application SHALL organize pytest tests in a tests directory

13.7. THE Application SHALL preserve the legacy prototype in a legacy directory as read-only reference

### Requirement 14: Input Validation

**User Story:** As an analyst, I want clear feedback when my input is invalid, so that I can correct issues and proceed with analysis.

#### Acceptance Criteria

14.1. WHEN a user provides invalid input, THE Input_Page SHALL display an error message describing the validation failure

14.2. WHEN a user uploads a file with invalid format, THE Input_Page SHALL display an error message specifying the expected formats

14.3. WHEN a user provides a URL that fails validation, THE Input_Page SHALL display an error message explaining the validation failure

14.4. THE Input_Page SHALL validate input before invoking any Tool

14.5. IF input validation fails, THEN THE Application SHALL NOT proceed with analysis

### Requirement 15: Error Handling

**User Story:** As an analyst, I want the application to handle errors gracefully, so that I can continue working even when individual operations fail.

#### Acceptance Criteria

15.1. WHEN a Tool encounters an error during analysis, THE Application SHALL display an error message to the user

15.2. WHEN a Tool encounters an error during analysis, THE Application SHALL NOT terminate

15.3. WHEN an Input_Reader encounters an error, THE Application SHALL display an error message describing the issue

15.4. WHEN an Input_Reader encounters an error, THE Application SHALL allow the user to retry with different input

15.5. IF a configuration file is missing or invalid, THEN THE Application SHALL use default configuration values and display a warning

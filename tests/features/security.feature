Feature: Security scanning with trufflehog

  Scenario: Trufflehog detects secrets in Python file
    Given the Python file "with_secret.py" exists
    When trufflehog is installed
    And `taidy lint with_secret.py` is run
    Then security scanning output is emitted
    And secrets are detected in the output

  Scenario: Trufflehog scans directory for secrets
    Given the Python file "with_secret.py" exists
    When trufflehog is installed
    And `taidy lint .` is run in the sample_files directory
    Then security scanning output is emitted
    And secrets are detected in the output

  Scenario: No security scanning when trufflehog not installed
    Given the Python file "with_secret.py" exists
    When trufflehog isn't installed
    And `taidy lint with_secret.py` is run
    Then no security scanning output is emitted
    And the command completes successfully